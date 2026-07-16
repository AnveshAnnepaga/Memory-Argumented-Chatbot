"""
Non-LLM Deterministic Tool Router (Milestone 13)

Classifies user requests using high-speed multi-pattern regex matching and
semantic keyword analysis to determine which external tool(s) should be invoked.
Never calls the LLM, ensuring 0ms latency and zero token cost for tool selection.
"""

import re
from typing import Dict, List, Set

from app.core.logger import get_logger

logger = get_logger("tool_router")

# Route Constants matching Milestone 13 specification
ROUTE_WEB_SEARCH = "WEB_SEARCH"
ROUTE_WEATHER = "WEATHER"
ROUTE_CALCULATOR = "CALCULATOR"
ROUTE_CURRENCY = "CURRENCY"
ROUTE_TIME = "TIME"
ROUTE_UNIT = "UNIT"
ROUTE_TRANSLATION = "TRANSLATION"
ROUTE_NO_TOOL = "NO_TOOL"

# Mapping between Route Constants and registered Tool Registry names
ROUTE_TO_TOOL_NAME: Dict[str, str] = {
    ROUTE_WEB_SEARCH: "web_search",
    ROUTE_WEATHER: "weather",
    ROUTE_CALCULATOR: "calculator",
    ROUTE_CURRENCY: "currency",
    ROUTE_TIME: "datetime",
    ROUTE_UNIT: "unit_converter",
    ROUTE_TRANSLATION: "translation",
}


class ToolRouter:
    """
    High-performance deterministic router for tool selection.
    Analyzes single and composite queries to return a list of required tool names.
    """
    def __init__(self) -> None:
        self._compiled_rules = [
            (
                ROUTE_WEATHER,
                re.compile(r"\b(weather|temperature|forecast|rain|cloudy|sunny|humidity|wind speed)\b", re.IGNORECASE)
            ),
            (
                ROUTE_UNIT,
                re.compile(r"\b(convert\s+\d+[\.\d]*\s*°?[cfk]|celsius|fahrenheit|kilometers?|miles?|pounds?|kilograms?|to\s+fahrenheit|to\s+celsius|°c|°f)\b", re.IGNORECASE)
            ),
            (
                ROUTE_CURRENCY,
                re.compile(r"\b(convert\s+\d+[\.\d]*\s*(usd|inr|eur|gbp|jpy|aud|cad)|exchange\s+rate|currency|dollars?\s+to\s+rupees?|rupees?\s+to\s+dollars?|usd\s+to\s+inr|inr\s+to\s+usd)\b", re.IGNORECASE)
            ),
            (
                ROUTE_CALCULATOR,
                re.compile(r"(\bcalculate\b|\bcompute\b|\bmath\b|\d+\s*[\+\-\*\/\^]\s*\d+|\bsqrt\s*\(|\bsin\s*\()", re.IGNORECASE)
            ),
            (
                ROUTE_TIME,
                re.compile(r"\b(current\s+time|what\s+time\s+is\s+it|current\s+date|today\'s\s+date|timezone|utc\s+time|local\s+time)\b", re.IGNORECASE)
            ),
            (
                ROUTE_TRANSLATION,
                re.compile(r"\b(translate|in\s+spanish|in\s+french|in\s+german|in\s+hindi|in\s+japanese|how\s+do\s+you\s+say\s+.+\s+in\s+[a-z]+)\b", re.IGNORECASE)
            ),
            (
                ROUTE_WEB_SEARCH,
                re.compile(r"\b(search\s+the\s+web|latest\s+news|web\s+search|who\s+won|current\s+events|google|search\s+online)\b", re.IGNORECASE)
            ),
        ]

    def classify_routes(self, query: str) -> List[str]:
        """
        Classifies the query into uppercase route constants.
        Returns a list of matching route constants or [ROUTE_NO_TOOL] if no tool is required.
        """
        if not query or not query.strip():
            return [ROUTE_NO_TOOL]

        clean_query = query.strip()
        matched_routes: List[str] = []
        seen: Set[str] = set()

        for route_const, pattern in self._compiled_rules:
            if pattern.search(clean_query):
                if route_const not in seen:
                    # Avoid duplicate trigger if e.g. "convert" triggers currency and unit, check specificity
                    matched_routes.append(route_const)
                    seen.add(route_const)

        if not matched_routes:
            logger.debug("No tool required for query: '%s' -> %s", clean_query[:40], ROUTE_NO_TOOL)
            return [ROUTE_NO_TOOL]

        logger.info("Classified tool routes for query '%s': %s", clean_query[:40], matched_routes)
        return matched_routes

    def route(self, query: str) -> List[str]:
        """
        Analyzes the request and returns a list of registered Tool Registry names
        (e.g., ['weather', 'unit_converter']) ready for execution.
        Returns empty list [] if NO_TOOL is selected.
        """
        routes = self.classify_routes(query)
        if ROUTE_NO_TOOL in routes or not routes:
            return []

        tool_names: List[str] = []
        for r in routes:
            t_name = ROUTE_TO_TOOL_NAME.get(r)
            if t_name and t_name not in tool_names:
                tool_names.append(t_name)

        return tool_names


# Global singleton router instance
tool_router = ToolRouter()
