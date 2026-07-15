# File: app/ingestion/crawler.py
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from app.ingestion.schemas import CrawlStatus, KnowledgeSourceSchema, RawDocument
from app.ingestion.source_registry import source_registry

logger = logging.getLogger("app.ingestion.crawler")


class WebCrawler:
    """
    (`8.2 Web Crawler`)
    Asynchronous web crawler responsible for downloading raw HTML from trusted knowledge sources.
    Responsibilities: Crawl pages, Download HTML, Respect robots.txt, Handle retries, Rate limiting, Return HTML.
    """

    def __init__(
        self,
        max_retries: int = 3,
        rate_limit_delay_sec: float = 1.0,
        timeout_sec: float = 15.0,
        user_agent: str = "Antigravity-Bot/1.0 (+https://github.com/Memory-Augmented-Chatbot)",
    ):
        self.max_retries = max_retries
        self.rate_limit_delay_sec = rate_limit_delay_sec
        self.timeout_sec = timeout_sec
        self.user_agent = user_agent
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self._last_request_time: Dict[str, float] = {}

    async def _check_robots_txt(self, url: str, client: httpx.AsyncClient) -> bool:
        """Checks target domain robots.txt to ensure our User-Agent is permitted (`Respect robots.txt`)."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain in self._robots_cache:
            return self._robots_cache[domain].can_fetch(self.user_agent, url)

        robots_url = urljoin(domain, "/robots.txt")
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            resp = await client.get(robots_url, timeout=5.0)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                # If robots.txt returns 404/403 or missing, assume allowed
                parser.parse(["User-agent: *", "Allow: /"])
        except Exception:
            parser.parse(["User-agent: *", "Allow: /"])

        self._robots_cache[domain] = parser
        return parser.can_fetch(self.user_agent, url)

    async def _enforce_rate_limit(self, domain: str) -> None:
        """Enforces per-domain rate limiting (`Rate limiting`)."""
        now = asyncio.get_event_loop().time()
        last = self._last_request_time.get(domain, 0.0)
        elapsed = now - last
        if elapsed < self.rate_limit_delay_sec:
            await asyncio.sleep(self.rate_limit_delay_sec - elapsed)
        self._last_request_time[domain] = asyncio.get_event_loop().time()

    async def fetch_page(
        self,
        url: str,
        source_name: str = "unknown",
        category: str = "general",
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[RawDocument]:
        """
        Downloads a single URL (`Download HTML`), handling retries (`Handle retries`) and robots.txt.
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        close_client = False
        if not client:
            client = httpx.AsyncClient(headers={"User-Agent": self.user_agent}, follow_redirects=True, timeout=self.timeout_sec)
            close_client = True

        try:
            # 1. Check robots.txt
            if not await self._check_robots_txt(url, client):
                logger.warning(f"[ROBOTS.TXT DENIED] URL '{url}' forbidden for {self.user_agent}")
                return None

            # 2. Rate limiting
            await self._enforce_rate_limit(domain)

            # 3. Download with exponential backoff retries
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.debug(f"Fetching '{url}' (Attempt {attempt}/{self.max_retries})...")
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        content_type = resp.headers.get("content-type", "").lower()
                        if "text/html" not in content_type and "application/xhtml+xml" not in content_type and not url.endswith((".html", ".htm", "/")):
                            logger.info(f"Skipping non-HTML URL '{url}' (Content-Type: {content_type})")
                            return None

                        return RawDocument(
                            url=str(resp.url),
                            source_name=source_name,
                            category=category,
                            raw_html=resp.text,
                            http_status=resp.status_code,
                            headers=dict(resp.headers),
                        )
                    elif resp.status_code in (404, 410, 403, 401):
                        logger.warning(f"URL '{url}' returned non-retryable HTTP {resp.status_code}")
                        break
                    else:
                        logger.warning(f"URL '{url}' returned HTTP {resp.status_code}. Retrying...")
                except (httpx.TimeoutException, httpx.NetworkError) as net_exc:
                    logger.warning(f"Network error on '{url}' (attempt {attempt}): {net_exc}")
                
                if attempt < self.max_retries:
                    await asyncio.sleep(2.0 ** attempt)
            
            logger.error(f"Failed to fetch '{url}' after {self.max_retries} attempts.")
            return None
        finally:
            if close_client and client:
                await client.aclose()

    async def crawl_source(self, source: KnowledgeSourceSchema, max_pages: int = 30, max_depth: int = 2) -> List[RawDocument]:
        """
        Crawls a registered source (`Crawl pages`) up to `max_pages` and `max_depth` using BFS.
        """
        if not source.enabled:
            logger.info(f"Source '{source.name}' is disabled. Skipping crawl.")
            return []

        source.status = CrawlStatus.CRAWLING
        raw_docs: List[RawDocument] = []
        visited_urls = set()
        queue = [(source.base_url, 0)]  # (url, depth)

        async with httpx.AsyncClient(headers={"User-Agent": self.user_agent}, follow_redirects=True, timeout=self.timeout_sec) as client:
            while queue and len(raw_docs) < max_pages:
                current_url, current_depth = queue.pop(0)
                if current_url in visited_urls:
                    continue
                visited_urls.add(current_url)

                if not source_registry.is_url_allowed(source.name, current_url):
                    continue

                doc = await self.fetch_page(url=current_url, source_name=source.name, category=source.category, client=client)
                if doc and doc.raw_html:
                    raw_docs.append(doc)
                    # Extract intra-domain links only if current_depth < max_depth and we need more pages
                    if len(raw_docs) < max_pages and current_depth < max_depth:
                        try:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(doc.raw_html, "lxml")
                            for a_tag in soup.find_all("a", href=True):
                                href = a_tag["href"]
                                full_url = urljoin(current_url, href)
                                parsed_link = urlparse(full_url)
                                if parsed_link.netloc == urlparse(source.base_url).netloc:
                                    clean_url = full_url.split("#")[0]
                                    if clean_url not in visited_urls and not any(q[0] == clean_url for q in queue):
                                        queue.append((clean_url, current_depth + 1))
                        except Exception as e:
                            logger.debug(f"Link extraction error on {current_url}: {e}")

        if raw_docs:
            source.status = CrawlStatus.COMPLETED
        else:
            source.status = CrawlStatus.FAILED

        logger.info(f"Crawled source '{source.name}': {len(raw_docs)} pages retrieved (Status: {source.status.value}, Max Depth: {max_depth})")
        return raw_docs


web_crawler = WebCrawler()
