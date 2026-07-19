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
ROUTE_NEWS_SEARCH = "NEWS_SEARCH"
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
    ROUTE_NEWS_SEARCH: "news_search",
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
                re.compile(r"\b(weather|wheather|temperature|forecast|rain|cloudy|sunny|humidity|wind speed)\b", re.IGNORECASE)
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
                ROUTE_NEWS_SEARCH,
                re.compile(r"\b(latest\s+news|breaking\s+news|news\s+about|news\s+on|latest\s+updates|recent\s+news|what\s+happened|breaking|headlines|news\s+headlines)\b", re.IGNORECASE)
            ),
            (
                ROUTE_WEB_SEARCH,
                re.compile(r"\b(search\s+the\s+web|latest\s+news|web\s+search|who\s+won|current\s+events|google|search\s+online|search\s+for|find\s+information|startup|startups|company|organization|firm|business|product)\b", re.IGNORECASE)
            ),
            # ── Roles / Positions ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"(who\s+is\s+(?:the\s+)?(?:current\s+|new\s+)?(?:president|prime\s*minister|captain|"
                    r"leader|CEO|director|chancellor|governor|mayor|chief|head|chairman|secretary|"
                    r"spokesperson|ambassador|manager|coach|winner|champion|incumbent|king|queen|emperor|ruler|"
                    r"owner|founder|ceo|cto|coo|president\s*elect)|"
                    r"who\s+was\s+(?:the\s+)?(?:president|prime\s*minister|captain|leader|king|queen|"
                    r"CEO|director|manager|coach|winner|champion|owner|incumbent)|"
                    r"(?:president|captain|prime\s*minister|PM|CEO|leader|king|queen|owner|"
                    r"winner|champion|incumbent)\s+of\s+(?:the\s+)?[A-Za-z]\w+|"
                    r"current\s+(?:president|captain|prime\s*minister|CEO|leader|king|queen|"
                    r"manager|coach|winner|champion|owner|incumbent|mayor)|"
                    r"who\s+(?:became|became\s+the|is\s+the\s+new|will\s+be\s+the\s+next)\s+"
                    r"(?:president|prime\s*minister|captain|leader|CEO|manager|coach|champion))",
                    re.IGNORECASE
                )
            ),
            # ── Sports scores / results / fixtures ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(score|scores|result|results|fixture|fixtures|match|matches|"
                    r"tournament|championship|champion|champions|winner|winners|"
                    r"standings|points\s+table|leaderboard|semi.?final|quarter.?final|"
                    r"playoff|play.?off|final|finals|"
                    r"[A-Z]\w+\s+(?:vs|v/s|versus)\s+[A-Z]\w+|"
                    r"who\s+won\s+(?:the\s+)?(?:match|game|series|ipl|world\s+cup|trophy|"
                    r"championship|final|tournament)|"
                    r"ipl\s+\d{4}|world\s+cup\s+\d{4}|"
                    r"cricket\s+score|football\s+score|soccer\s+score|basketball\s+score)\b",
                    re.IGNORECASE
                )
            ),
            # ── Finance: stocks, crypto, markets ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(stock\s+price|share\s+price|crypto\s+price|bitcoin|ethereum|"
                    r"solana|dogecoin|ripple|cryptocurrency|"
                    r"market\s+cap|nifty|sensex|dow\s+jones|nasdaq|s&p\s+500|"
                    r"stock\s+market|share\s+market|bullion|gold\s+price|silver\s+price|"
                    r"mutual\s+fund|index\s+fund|etf|ipo|"
                    r"\b[A-Z]{2,5}\s+stock\b|\b\$[A-Z]{2,5}\b|"
                    r"price\s+of\s+(?:bitcoin|ethereum|gold|silver|oil))\b",
                    re.IGNORECASE
                )
            ),
            # ── Prices / costs ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(price\s+of|cost\s+of|how\s+much\s+(?:is|does|are|were)|"
                    r"what\s+(?:is|are)\s+the\s+price|what\s+(?:is|are)\s+the\s+cost|"
                    r"how\s+much\s+does\s+it\s+cost|"
                    r"what\s+(?:is|are)\s+the\s+(?:current|latest)\s+(?:price|rate|cost))\b",
                    re.IGNORECASE
                )
            ),
            # ── Statistics / data (population, GDP, rates) ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(population\s+of|GDP\s+of|gdp\s+of|inflation\s+rate|"
                    r"unemployment\s+rate|interest\s+rate|exchange\s+rate|"
                    r"birth\s+rate|death\s+rate|literacy\s+rate|"
                    r"census\s+\d{4}|"
                    r"what\s+(?:is|are)\s+the\s+(?:current|latest)\s+(?:population|gdp|inflation|"
                    r"unemployment|interest\s+rate))\b",
                    re.IGNORECASE
                )
            ),
            # ── Time-sensitive knowledge (current / latest / recent / today / year) ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(current\s+(?:population|gdp|inflation|unemployment|weather|"
                    r"temperature|time|date|status|situation|condition|"
                    r"president|prime\s*minister|captain|CEO|leader|manager|"
                    r"price|rate|value|score|result|news|events|"
                    r"population|GDP|economy|market|stock|share|index)|"
                    r"latest\s+(?:news|update|updates|information|data|figures|stats|"
                    r"technology|tech|model|version|release|edition|"
                    r"price|prices|rate|rates|score|scores|result|results|"
                    r"movie|film|album|song|trend|trends|developments|"
                    r"report|reports|study|studies|research|findings)|"
                    r"recent\s+(?:news|events|developments|updates|changes|"
                    r"releases|announcements|reports|studies|"
                    r"price|rate|score|result|match|election)|"
                    r"today'?s\s+(?:news|weather|date|headlines|"
                    r"result|score|match|price|rate|exchange\s+rate|"
                    r"stock|market|cricket|football|sports)|"
                    r"what\s+(?:happened|occurred|took\s+place)\s+(?:today|yesterday|"
                    r"this\s+week|this\s+month|this\s+year|recently|lately)|"
                    r"this\s+(?:week|month|quarter|year)'?s?\s+(?:news|update|result|"
                    r"election|report|sales|earnings|performance))\b",
                    re.IGNORECASE
                )
            ),
            # ── Year markers ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(?:20[2-9][4-9]|20[3-9][0-9])\s+(?:election|result|winner|"
                    r"president|captain|champion|championship|olympics|"
                    r"world\s+cup|t20|odi|test|series|tournament|"
                    r"budget|GDP|population|census|"
                    r"price|rate|sales|revenue|profit|"
                    r"model|version|release|edition)\b",
                    re.IGNORECASE
                )
            ),
            # ── Entertainment (box office, ratings, awards) ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(box\s+office|highest\s+grossing|ratings|viewership|trp|"
                    r"oscar|grammy|emmy|tony|golden\s+globe|"
                    r"blockbuster|hit\s+movie|hit\s+film|top\s+rated|"
                    r"most\s+watched|most\s+popular|trending|viral)\b",
                    re.IGNORECASE
                )
            ),
            # ── Technology (releases, announcements, versions) ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(newly\s+released|newly\s+launched|just\s+released|just\s+launched|"
                    r"latest\s+(?:version|update|release|model|edition|os|android|ios|"
                    r"iphone|samsung|pixel|windows|macos)|"
                    r"upcoming\s+(?:phone|model|device|version|release|launch|event)|"
                    r"\b(?:released|launched|announced)\s+(?:today|yesterday|this\s+week))\b",
                    re.IGNORECASE
                )
            ),
            # ── Geo / place facts (capital, population, area) ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"\b(capital\s+of|population\s+of|area\s+of|largest\s+city\s+in|"
                    r"official\s+language\s+of|currency\s+of|timezone\s+of|"
                    r"what\s+is\s+the\s+(?:capital|population|area|currency|language)\s+of)\b",
                    re.IGNORECASE
                )
            ),
            # ── General catch-all for time-sensitive facts ──
            (
                ROUTE_WEB_SEARCH,
                re.compile(
                    r"(what\s+(?:is|are)\s+the\s+(?:current|latest|new|recent)\s+\w+|"
                    r"who\s+(?:is|are)\s+the\s+(?:current|latest|new|recent)\s+\w+|"
                    r"(?:what|who)\s+(?:is|are)\s+the\s+(?:latest|newest|most\s+recent)|"
                    r"tell\s+me\s+(?:about|the)\s+(?:current|latest|recent)\s+\w+)",
                    re.IGNORECASE
                )
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
