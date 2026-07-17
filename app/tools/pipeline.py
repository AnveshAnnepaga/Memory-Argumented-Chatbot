"""
Tool Pipeline Orchestrator (Milestone 13)

Orchestrates the complete flow from raw user query through deterministic routing,
validation, high-performance execution, and clean output formatting for downstream
LangGraph context merge and LLM prompt building.
"""

import json
from typing import List, Optional, Tuple

from app.core.logger import get_logger
from app.tools.manager import tool_manager
from app.tools.schemas import ToolResponse

logger = get_logger("tool_pipeline")


class ToolPipeline:
    """
    End-to-end pipeline processing user queries for tool invocation.
    Formats successful tool results into clean Markdown context blocks.
    """
    def __init__(self) -> None:
        pass

    async def process_query(
        self,
        user_query: str,
        user_id: str = "default",
        session_id: str = "default",
        tool_names: Optional[List[str]] = None,
        mode: str = "parallel"
    ) -> Tuple[List[ToolResponse], str]:
        """
        Runs the full tool execution pipeline for the given user query.
        Returns a tuple containing the list of ToolResponses and the formatted Markdown context block.
        If no tools execute, returns ([], "").
        """
        responses = await tool_manager.execute_tools(
            query=user_query,
            tool_names=tool_names,
            user_id=user_id,
            session_id=session_id,
            mode=mode
        )

        if not responses:
            return [], ""

        formatted_block = self.format_context(responses)
        logger.info("ToolPipeline successfully generated %d tool responses for query: '%s'", len(responses), user_query[:40])
        return responses, formatted_block

    def format_context(self, responses: List[ToolResponse]) -> str:
        """
        Formats normalized tool responses into a structured Markdown block
        suitable for direct injection into the LangGraph final_context.

        Output is intentionally minimal: it only carries the tool's data payload
        (e.g. weather fields, calculator result). No headers like
        "REAL-TIME EXTERNAL TOOL INTELLIGENCE", no Exec Time, no Cached flag,
        no status string - because those would otherwise leak into the user-facing
        answer and force the LLM to mention "based on a tool".
        """
        if not responses:
            return ""

        lines: List[str] = []
        for resp in responses:
            if resp.success and resp.data is not None:
                if isinstance(resp.data, (dict, list)):
                    try:
                        data_str = json.dumps(resp.data, ensure_ascii=False, indent=2)
                    except Exception:
                        data_str = str(resp.data)
                else:
                    data_str = str(resp.data)
                lines.append(data_str)
            elif resp.error:
                lines.append(f"Tool error: {resp.error}")

        return "\n\n".join(lines).strip()


# Global singleton pipeline instance
tool_pipeline = ToolPipeline()
