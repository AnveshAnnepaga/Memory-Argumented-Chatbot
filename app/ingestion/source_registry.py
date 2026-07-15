# File: app/ingestion/source_registry.py
import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urlparse
import yaml
from app.ingestion.schemas import (
    CrawlStatus,
    KnowledgeSourceSchema,
    PriorityLevel,
    TrustLevel,
)

logger = logging.getLogger("app.ingestion.source_registry")


class SourceRegistry:
    """
    (`8.1 Source Registry`)
    Centralized registry managing trusted knowledge sources loaded dynamically from `sources.yaml`.
    Responsibilities: Register websites, Organize by category, Enable/Disable sources,
    Assign crawl priority, Define allowed paths, Define excluded paths.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._sources: Dict[str, KnowledgeSourceSchema] = {}
        if not config_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "sources.yaml")
        self.config_path = config_path
        self.load_from_yaml(self.config_path)

    def load_from_yaml(self, filepath: str) -> int:
        """Loads or reloads trusted knowledge sources from YAML config."""
        if not os.path.exists(filepath):
            logger.warning(f"Source config file not found at {filepath}. Starting with empty registry.")
            return 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            count = 0
            for category, items in data.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    name = item.get("name", "").strip()
                    url = item.get("url", "").strip()
                    if not name or not url:
                        continue
                    trust = TrustLevel(item.get("trust", "tier1").lower())
                    priority = PriorityLevel(item.get("priority", "high").lower())
                    allowed = item.get("allowed_paths", [])
                    excluded = item.get("excluded_paths", [])
                    freq = int(item.get("crawl_frequency_hours", 24))

                    source = KnowledgeSourceSchema(
                        name=name,
                        category=category,
                        base_url=url,
                        trust_level=trust,
                        priority=priority,
                        enabled=item.get("enabled", True),
                        allowed_paths=allowed if isinstance(allowed, list) else [str(allowed)],
                        excluded_paths=excluded if isinstance(excluded, list) else [str(excluded)],
                        crawl_frequency_hours=freq,
                        status=CrawlStatus.PENDING,
                    )
                    self._sources[name] = source
                    count += 1
            logger.info(f"Successfully loaded {count} trusted sources from {filepath}.")
            return count
        except Exception as exc:
            logger.error(f"Failed to load YAML sources from {filepath}: {exc}", exc_info=True)
            return len(self._sources)

    def register_source(self, source: KnowledgeSourceSchema) -> KnowledgeSourceSchema:
        """Dynamically registers or updates a knowledge source."""
        self._sources[source.name] = source
        logger.debug(f"Registered source: '{source.name}' ({source.category} | {source.trust_level.value})")
        return source

    def get_source(self, name: str) -> Optional[KnowledgeSourceSchema]:
        """Retrieves a source by name."""
        return self._sources.get(name)

    def list_sources(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
        trust_level: Optional[TrustLevel] = None,
        priority: Optional[PriorityLevel] = None,
    ) -> List[KnowledgeSourceSchema]:
        """Returns a filtered list of registered knowledge sources ordered by priority."""
        sources = list(self._sources.values())
        if enabled_only:
            sources = [s for s in sources if s.enabled]
        if category:
            sources = [s for s in sources if s.category.lower() == category.lower()]
        if trust_level:
            sources = [s for s in sources if s.trust_level == trust_level]
        if priority:
            sources = [s for s in sources if s.priority == priority]

        # Order by priority: high -> medium -> low
        priority_order = {PriorityLevel.HIGH: 0, PriorityLevel.MEDIUM: 1, PriorityLevel.LOW: 2}
        sources.sort(key=lambda x: priority_order.get(x.priority, 99))
        return sources

    def enable_source(self, name: str) -> bool:
        """Enables a registered source (`Enable/Disable sources`)."""
        if name in self._sources:
            self._sources[name].enabled = True
            logger.info(f"Enabled source '{name}'")
            return True
        return False

    def disable_source(self, name: str) -> bool:
        """Disables a registered source (`Enable/Disable sources`)."""
        if name in self._sources:
            self._sources[name].enabled = False
            logger.info(f"Disabled source '{name}'")
            return True
        return False

    def update_priority(self, name: str, priority: PriorityLevel) -> bool:
        """Updates crawl priority for a source (`Assign crawl priority`)."""
        if name in self._sources:
            self._sources[name].priority = priority
            logger.info(f"Updated priority for '{name}' to {priority.value}")
            return True
        return False

    def is_url_allowed(self, source_name: str, url: str) -> bool:
        """
        Validates if a specific target URL matches `allowed_paths` and is not inside `excluded_paths`
        (`Define allowed paths` / `Define excluded paths`).
        """
        source = self._sources.get(source_name)
        if not source or not source.enabled:
            return False

        parsed = urlparse(url)
        path = parsed.path or "/"

        # Check exclusions first
        for exc in source.excluded_paths:
            if exc and exc in path:
                return False

        # Check inclusions (if allowed_paths is specified, URL must match at least one)
        if source.allowed_paths and len(source.allowed_paths) > 0:
            if not any(allow and allow in path for allow in source.allowed_paths):
                # Allow the base URL exactly
                if url.rstrip("/") != source.base_url.rstrip("/"):
                    return False

        return True


source_registry = SourceRegistry()
