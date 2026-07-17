import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from xml.etree import ElementTree
from app.ingestion.schemas import CrawlStatus, KnowledgeSourceSchema, RawDocument
from app.ingestion.source_registry import source_registry

logger = logging.getLogger("app.ingestion.crawler")


class WebCrawler:
    """
    (`8.2 Web Crawler`)
    Asynchronous web crawler with sitemap discovery, concurrent downloads,
    robots.txt respect, rate limiting, and retry logic.
    """

    def __init__(
        self,
        max_retries: int = 3,
        rate_limit_delay_sec: float = 0.5,
        timeout_sec: float = 15.0,
        max_concurrent: int = 10,
        user_agent: str = "Vyron-Bot/1.0 (+https://github.com/Memory-Augmented-Chatbot)",
    ):
        self.max_retries = max_retries
        self.rate_limit_delay_sec = rate_limit_delay_sec
        self.timeout_sec = timeout_sec
        self.max_concurrent = max_concurrent
        self.user_agent = user_agent
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self._last_request_time: Dict[str, float] = {}
        self._semaphore: asyncio.Semaphore | None = None

    async def _check_robots_txt(self, url: str, client: httpx.AsyncClient) -> bool:
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
                parser.parse(["User-agent: *", "Allow: /"])
        except Exception:
            parser.parse(["User-agent: *", "Allow: /"])
        self._robots_cache[domain] = parser
        return parser.can_fetch(self.user_agent, url)

    async def _enforce_rate_limit(self, domain: str) -> None:
        now = asyncio.get_event_loop().time()
        last = self._last_request_time.get(domain, 0.0)
        elapsed = now - last
        if elapsed < self.rate_limit_delay_sec:
            await asyncio.sleep(self.rate_limit_delay_sec - elapsed)
        self._last_request_time[domain] = asyncio.get_event_loop().time()

    async def _fetch_sitemap(self, base_url: str, client: httpx.AsyncClient) -> List[str]:
        """Discover and parse sitemap.xml. Supports sitemap indexes."""
        sitemap_urls = [
            urljoin(base_url, "/sitemap.xml"),
            urljoin(base_url, "/sitemap_index.xml"),
            urljoin(base_url, "/sitemap/"),
        ]
        all_locs: List[str] = []
        for s_url in sitemap_urls:
            try:
                resp = await client.get(s_url, timeout=10.0)
                if resp.status_code != 200:
                    continue
                root = ElementTree.fromstring(resp.content)
                ns = re.match(r"\{.*\}", root.tag)
                ns = ns.group(0) if ns else ""
                # Sitemap index
                for sm in root.findall(f"{ns}sitemap"):
                    loc_el = sm.find(f"{ns}loc")
                    if loc_el is not None and loc_el.text:
                        nested = await self._fetch_single_sitemap(loc_el.text.strip(), client)
                        all_locs.extend(nested)
                # Standard urlset
                for url_el in root.findall(f"{ns}url"):
                    loc_el = url_el.find(f"{ns}loc")
                    if loc_el is not None and loc_el.text:
                        all_locs.append(loc_el.text.strip())
                if all_locs:
                    logger.info(f"Sitemap found at {s_url}: {len(all_locs)} URLs")
                    return all_locs
            except Exception as e:
                logger.debug(f"Sitemap fetch failed for {s_url}: {e}")
        return []

    async def _fetch_single_sitemap(self, sitemap_url: str, client: httpx.AsyncClient) -> List[str]:
        locs: List[str] = []
        try:
            resp = await client.get(sitemap_url, timeout=10.0)
            if resp.status_code != 200:
                return locs
            root = ElementTree.fromstring(resp.content)
            ns = re.match(r"\{.*\}", root.tag)
            ns = ns.group(0) if ns else ""
            for url_el in root.findall(f"{ns}url"):
                loc_el = url_el.find(f"{ns}loc")
                if loc_el is not None and loc_el.text:
                    locs.append(loc_el.text.strip())
        except Exception as e:
            logger.debug(f"Nested sitemap fetch failed: {e}")
        return locs

    async def fetch_page(
        self,
        url: str,
        source_name: str = "unknown",
        category: str = "general",
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[RawDocument]:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        close_client = False
        if not client:
            client = httpx.AsyncClient(headers={"User-Agent": self.user_agent}, follow_redirects=True, timeout=self.timeout_sec)
            close_client = True

        sem = self._semaphore or asyncio.Semaphore(self.max_concurrent)

        try:
            if not await self._check_robots_txt(url, client):
                logger.warning(f"[ROBOTS.TXT DENIED] '{url}'")
                return None
            await self._enforce_rate_limit(domain)

            for attempt in range(1, self.max_retries + 1):
                try:
                    async with sem:
                        logger.debug(f"Fetching '{url}' (Attempt {attempt}/{self.max_retries})...")
                        resp = await client.get(url)
                    if resp.status_code == 200:
                        ct = resp.headers.get("content-type", "").lower()
                        if "text/html" not in ct and "application/xhtml+xml" not in ct and not url.endswith((".html", ".htm", "/")):
                            logger.debug(f"Skipping non-HTML '{url}' ({ct})")
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
                        logger.warning(f"URL '{url}' returned HTTP {resp.status_code}")
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

    async def crawl_source(
        self, source: KnowledgeSourceSchema, max_pages: Optional[int] = None, max_depth: Optional[int] = None
    ) -> List[RawDocument]:
        if not source.enabled:
            logger.info(f"Source '{source.name}' is disabled. Skipping.")
            return []

        pages = max_pages or source.max_pages
        depth = max_depth or source.max_depth
        source.status = CrawlStatus.CRAWLING
        raw_docs: List[RawDocument] = []
        visited_urls: Set[str] = set()

        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent}, follow_redirects=True, timeout=self.timeout_sec
        ) as client:
            # Step 1: Try sitemap first (most complete)
            sitemap_urls: List[str] = []
            if source.use_sitemap:
                sitemap_urls = await self._fetch_sitemap(source.base_url, client)
                logger.info(f"Sitemap for '{source.name}' yielded {len(sitemap_urls)} URLs")

            if sitemap_urls:
                # Filter sitemap URLs through allowed_paths / excluded_paths
                valid_sitemap_urls = [
                    u for u in sitemap_urls
                    if source_registry.is_url_allowed(source.name, u) and u not in visited_urls
                ]
                logger.info(f"After path filtering: {len(valid_sitemap_urls)} URLs from sitemap")

                # Crawl concurrently with semaphore
                sem = asyncio.Semaphore(self.max_concurrent)
                self._semaphore = sem

                async def _crawl_sitemap_url(u: str) -> Optional[RawDocument]:
                    if u in visited_urls or len(raw_docs) >= pages:
                        return None
                    visited_urls.add(u)
                    return await self.fetch_page(url=u, source_name=source.name, category=source.category, client=client)

                batch = valid_sitemap_urls[:pages]
                tasks = [_crawl_sitemap_url(u) for u in batch]
                for coro in asyncio.as_completed(tasks):
                    if len(raw_docs) >= pages:
                        break
                    doc = await coro
                    if doc and doc.raw_html:
                        raw_docs.append(doc)

            # Step 2: BFS fallback (if sitemap gave fewer pages than requested)
            if len(raw_docs) < pages:
                queue = [(source.base_url, 0)]
                while queue and len(raw_docs) < pages:
                    current_url, current_depth = queue.pop(0)
                    if current_url in visited_urls:
                        continue
                    visited_urls.add(current_url)

                    if not source_registry.is_url_allowed(source.name, current_url):
                        continue

                    doc = await self.fetch_page(url=current_url, source_name=source.name, category=source.category, client=client)
                    if doc and doc.raw_html:
                        raw_docs.append(doc)
                        if len(raw_docs) < pages and current_depth < depth:
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

        source.status = CrawlStatus.COMPLETED if raw_docs else CrawlStatus.FAILED
        logger.info(
            f"Crawled '{source.name}': {len(raw_docs)} pages (Status: {source.status.value}, Max: {pages}, Depth: {depth})"
        )
        return raw_docs


web_crawler = WebCrawler()
