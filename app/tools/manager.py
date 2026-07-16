"""
Tool Manager Facade (Milestone 13)

Acts as the central facade for tool execution, validating inputs against schemas,
coordinating single and batch executions via the ToolExecutor, and normalizing
outputs. Completely decoupled from LangGraph and downstream orchestration.
"""

from typing import Any, Dict, List, Optional

from app.core.logger import get_logger
from app.tools.executor import tool_executor
from app.tools.registry import tool_registry
from app.tools.router import tool_router
from app.tools.schemas import ToolRequest, ToolResponse

logger = get_logger("tool_manager")


class ToolManager:
    """
    Central manager for external tool operations.
    Validates requests, invokes the executor, and returns normalized responses.
    """
    def __init__(self) -> None:
        pass

    async def execute_tools(
        self,
        query: str,
        tool_names: Optional[List[str]] = None,
        parameters_map: Optional[Dict[str, Dict[str, Any]]] = None,
        user_id: str = "default",
        session_id: str = "default",
        mode: str = "parallel"
    ) -> List[ToolResponse]:
        """
        Executes one or more tools for a given user query.
        If tool_names is not explicitly provided, uses the deterministic ToolRouter.
        """
        params_map = parameters_map or {}
        
        # 1. Determine target tools
        target_tools = tool_names
        if target_tools is None:
            target_tools = tool_router.route(query)
            
        if not target_tools:
            logger.debug("No tools targeted or routed for query: '%s'", query[:40])
            return []

        logger.info("Executing tools %s in %s mode for query: '%s'", target_tools, mode.upper(), query[:40])

        # 2. Build validated requests
        requests: List[ToolRequest] = []
        for t_name in target_tools:
            definition = tool_registry.get_tool(t_name)
            if not definition:
                logger.warning("Targeted tool '%s' not found in registry. Skipping.", t_name)
                continue

            # Check for custom parameters or pass full query
            tool_params = params_map.get(t_name, {})
            # Basic validation check against required properties if defined
            req_fields = definition.input_schema.get("required", [])
            for field in req_fields:
                if field not in tool_params and field == "query":
                    tool_params["query"] = query

            req = ToolRequest(
                query=query,
                tool_name=definition.name,
                parameters=tool_params,
                user_id=user_id,
                session_id=session_id
            )
            requests.append(req)

        if not requests:
            return []

        # 3. Execute via ToolExecutor
        if len(requests) == 1:
            resp = await tool_executor.execute_single(requests[0])
            return [resp]
        else:
            responses = await tool_executor.execute_batch(requests, mode=mode)
            return responses

    async def execute_tool_by_name(
        self,
        tool_name: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: str = "default",
        session_id: str = "default"
    ) -> ToolResponse:
        """Convenience method to execute a specific tool directly by name."""
        req = ToolRequest(
            query=query,
            tool_name=tool_name,
            parameters=parameters or {},
            user_id=user_id,
            session_id=session_id
        )
        return await tool_executor.execute_single(req)


# Global singleton manager instance
tool_manager = ToolManager()
