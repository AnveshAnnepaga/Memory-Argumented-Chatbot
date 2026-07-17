import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("app.ingestion.parsers")


@dataclass
class FileParseResult:
    text: str
    title: str
    file_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_bytes: Optional[bytes] = None


class FileParserRegistry:
    """Routes file parsing by MIME type / extension. Supports both sync and async parsers."""

    def __init__(self):
        self._parsers: Dict[str, object] = {}

    def register(self, mime_type: str, parser: object) -> None:
        self._parsers[mime_type] = parser

    def get_parser(self, mime_type: str):
        parser = self._parsers.get(mime_type)
        if not parser:
            for pattern, p in self._parsers.items():
                if pattern.endswith("*") and mime_type.startswith(pattern[:-1]):
                    return p
        return parser

    async def parse(self, file_bytes: bytes, filename: str, mime_type: str) -> Optional[FileParseResult]:
        parser = self.get_parser(mime_type)
        if parser is None:
            logger.warning(f"No parser registered for MIME type '{mime_type}' (file: {filename})")
            return None
        try:
            method = parser.parse
            if inspect.iscoroutinefunction(method):
                return await method(file_bytes, filename)
            return method(file_bytes, filename)
        except Exception as e:
            logger.error(f"Parser failed for '{filename}' ({mime_type}): {e}")
            return None


file_parser_registry = FileParserRegistry()
