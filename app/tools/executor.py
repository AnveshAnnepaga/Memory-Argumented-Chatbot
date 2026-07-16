"""
High-Performance Tool Executor (Milestone 13)

Responsible for executing external tools with robust resiliency mechanisms:
exponential backoff retries, strict timeout enforcement, thread-safe TTL caching,
concurrency rate limiting, and execution timing metadata.
Supports single tool, parallel batch, and sequential priority batch execution.
"""

import asyncio
import inspect
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.logger import get_logger
from app.tools.registry import tool_registry
from app.tools.schemas import ToolDefinition, ToolRequest, ToolResponse

logger = get_logger("tool_executor")


class TTLCache:
    """Thread-safe in-memory cache supporting time-to-live (TTL) expiration."""
    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                expires_at, data = self._cache[key]
                if time.time() < expires_at:
                    return data
                else:
                    del self._cache[key]
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        async with self._lock:
            expires_at = time.time() + ttl_seconds
            self._cache[key] = (expires_at, value)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()


class ToolExecutor:
    """
    Executes tool requests against registered tool definitions.
    Implements retry, timeout, caching, rate limiting, and parallel/sequential execution.
    """
    def __init__(self, max_retries: int = 2, base_backoff_sec: float = 0.5) -> None:
        self._cache = TTLCache()
        self._max_retries = max_retries
        self._base_backoff = base_backoff_sec
        # Rate limiting semaphore (max 20 concurrent executions)
        self._semaphore = asyncio.Semaphore(20)

    def _generate_cache_key(self, tool_name: str, parameters: Dict[str, Any], query: str) -> str:
        """Generates a stable cache key based on tool name and inputs."""
        payload = {"params": parameters, "q": query.strip().lower()}
        try:
            sorted_payload = json.dumps(payload, sort_keys=True)
        except Exception:
            sorted_payload = str(payload)
        return f"tool:{tool_name.lower()}:{sorted_payload}"

    async def execute_single(self, request: ToolRequest, override_definition: Optional[ToolDefinition] = None) -> ToolResponse:
        """
        Executes a single tool request with retry, timeout, and caching support.
        Always returns a standardized ToolResponse (never raises raw exceptions).
        """
        start_time = time.perf_counter()
        tool_name = request.tool_name
        if not tool_name:
            return ToolResponse(
                success=False,
                tool_name="unknown",
                error="ToolRequest missing explicit tool_name.",
                execution_time_ms=0.0
            )

        definition = override_definition or tool_registry.get_tool(tool_name)
        if not definition:
            return ToolResponse(
                success=False,
                tool_name=tool_name,
                error=f"Tool '{tool_name}' is not registered in ToolRegistry.",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # 1. Check TTL Cache
        if definition.cache_ttl_seconds > 0:
            cache_key = self._generate_cache_key(definition.name, request.parameters, request.query)
            cached_data = await self._cache.get(cache_key)
            if cached_data is not None:
                logger.debug("Cache hit for tool '%s' [Key: %s]", definition.name, cache_key[:40])
                exec_time = (time.perf_counter() - start_time) * 1000
                return ToolResponse(
                    success=True,
                    tool_name=definition.name,
                    data=cached_data,
                    execution_time_ms=round(exec_time, 2),
                    cached=True,
                    metadata={"source_api": definition.category, "cached": True}
                )

        if not definition.handler:
            return ToolResponse(
                success=False,
                tool_name=definition.name,
                error=f"Tool '{definition.name}' has no execution handler defined.",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # 2. Execute with Semaphore, Retries, and Strict Timeout
        last_error: Optional[str] = None
        for attempt in range(1, self._max_retries + 2):
            try:
                async with self._semaphore:
                    logger.debug("Executing tool '%s' (Attempt %d/%d)", definition.name, attempt, self._max_retries + 1)
                    if inspect.iscoroutinefunction(definition.handler):
                        raw_result = await asyncio.wait_for(definition.handler(request), timeout=definition.timeout)
                    else:
                        # Sync function wrapped in executor
                        raw_result = await asyncio.wait_for(
                            asyncio.to_thread(definition.handler, request),
                            timeout=definition.timeout
                        )

                # Execution succeeded -> Store in cache and return
                exec_time = (time.perf_counter() - start_time) * 1000
                if definition.cache_ttl_seconds > 0:
                    cache_key = self._generate_cache_key(definition.name, request.parameters, request.query)
                    await self._cache.set(cache_key, raw_result, definition.cache_ttl_seconds)

                return ToolResponse(
                    success=True,
                    tool_name=definition.name,
                    data=raw_result,
                    execution_time_ms=round(exec_time, 2),
                    cached=False,
                    metadata={"source_api": definition.category, "attempts": attempt}
                )

            except asyncio.TimeoutError:
                last_error = f"Tool execution timed out after {definition.timeout} seconds."
                logger.warning("Timeout executing tool '%s' on attempt %d: %s", definition.name, attempt, last_error)
            except Exception as e:
                last_error = str(e)
                logger.warning("Error executing tool '%s' on attempt %d: %s", definition.name, attempt, last_error)

            # Exponential backoff before retry if attempts remain
            if attempt <= self._max_retries:
                backoff = self._base_backoff * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        # All retries exhausted or fatal error
        exec_time = (time.perf_counter() - start_time) * 1000
        return ToolResponse(
            success=False,
            tool_name=definition.name,
            error=last_error or "Unknown tool execution failure.",
            execution_time_ms=round(exec_time, 2),
            cached=False,
            metadata={"source_api": definition.category, "attempts": self._max_retries + 1}
        )

    async def execute_batch(self, requests: List[ToolRequest], mode: str = "parallel") -> List[ToolResponse]:
        """
        Executes a batch of tool requests either in parallel (via asyncio.gather)
        or sequentially (ordered by tool priority).
        """
        if not requests:
            return []

        if mode.lower() == "parallel":
            logger.info("Executing batch of %d tool requests in PARALLEL mode.", len(requests))
            tasks = [self.execute_single(req) for req in requests]
            responses = await asyncio.gather(*tasks, return_exceptions=False)
            return list(responses)
        else:
            # Sequential mode ordered by priority (lower number = higher priority)
            logger.info("Executing batch of %d tool requests in SEQUENTIAL mode.", len(requests))
            # Sort requests by priority from ToolRegistry
            def _get_priority(req: ToolRequest) -> int:
                if req.tool_name:
                    t = tool_registry.get_tool(req.tool_name)
                    if t:
                        return t.priority
                return 100

            sorted_requests = sorted(requests, key=_get_priority)
            responses: List[ToolResponse] = []
            for req in sorted_requests:
                resp = await self.execute_single(req)
                responses.append(resp)
            return responses

    async def clear_cache(self) -> None:
        """Clear all cached tool responses."""
        await self._cache.clear()


# Global singleton executor instance
tool_executor = ToolExecutor()
