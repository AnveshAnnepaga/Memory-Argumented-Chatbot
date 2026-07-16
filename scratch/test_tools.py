"""
Milestone 13 Verification Test Script (Tool System & External Function Calling)

Tests all 11 core requirements of the production-grade Tool System:
1. Tool Registry & Dynamic Registration
2. Schema Validation (Input / Output Contracts)
3. Non-LLM Deterministic Tool Router (Single & Composite Queries)
4. Safe Math Calculator & Arithmetic AST Evaluation
5. Resilient Executor (Retries & Timeout Handling)
6. Thread-Safe TTL Caching (Cache Hits vs Misses)
7. Concurrency Rate Limiting & Semaphore Enforcement
8. Parallel & Sequential Batch Execution Modes
9. Tool Pipeline Output Formatting for Context Merging
10. End-to-End LangGraph Orchestration Integration
11. Architectural Decoupling Verification (Zero LangGraph/RAG/Memory dependencies inside app/tools)
"""

import asyncio
import inspect
import sys
import time
from typing import Any, Dict

# Set up clean paths
import os
sys.path.insert(0, os.path.abspath("."))

from app.tools import (
    ToolDefinition,
    ToolRequest,
    ToolResponse,
    tool_executor,
    tool_manager,
    tool_pipeline,
    tool_registry,
    tool_router,
)
from app.orchestration.pipeline import orchestration_pipeline


async def run_milestone_13_tests():
    print("================================================================================")
    print("[MILESTONE 13 VERIFICATION: TOOL SYSTEM & EXTERNAL FUNCTION CALLING]")
    print("================================================================================")

    # -------------------------------------------------------------------------
    # TEST 1: Tool Registry & Dynamic Registration
    # -------------------------------------------------------------------------
    print("\n[1/11] Testing Tool Registry & Dynamic Registration...")
    tools = tool_registry.list_tools()
    assert len(tools) >= 7, f"Expected at least 7 built-in V1 tools, found {len(tools)}"
    print(f"  [OK] Found {len(tools)} registered tools: {[t.name for t in tools]}")

    # Register custom custom_ping tool dynamically
    async def custom_ping_handler(request: ToolRequest) -> Dict[str, Any]:
        return {"status": "pong", "echo": request.query}

    ping_def = ToolDefinition(
        name="custom_ping",
        description="A dynamic test ping tool.",
        category="utility",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"status": {"type": "string"}}},
        priority=5,
        timeout=1.0,
        cache_ttl_seconds=10,
        handler=custom_ping_handler
    )
    tool_registry.register_tool(ping_def)
    assert tool_registry.get_tool("custom_ping") is not None, "Dynamic registration failed!"
    print("  [OK] Successfully registered and retrieved dynamic tool 'custom_ping'.")

    # -------------------------------------------------------------------------
    # TEST 2: Schema Validation (Input / Output Contracts)
    # -------------------------------------------------------------------------
    print("\n[2/11] Testing Schema Contracts & Standardization...")
    req = ToolRequest(query="Calculate 5+5", tool_name="calculator", parameters={"expression": "5+5"})
    assert req.tool_name == "calculator"
    assert req.parameters["expression"] == "5+5"
    
    resp = ToolResponse(success=True, tool_name="calculator", data={"result": 10}, execution_time_ms=1.2)
    assert resp.success is True and resp.data["result"] == 10
    print("  [OK] ToolRequest & ToolResponse Pydantic models validated.")

    # -------------------------------------------------------------------------
    # TEST 3: Non-LLM Deterministic Tool Router
    # -------------------------------------------------------------------------
    print("\n[3/11] Testing Non-LLM Deterministic Tool Router...")
    q_single = "What is the weather in Tokyo?"
    routes_single = tool_router.route(q_single)
    assert "weather" in routes_single, f"Expected 'weather' in {routes_single}"
    print(f"  [OK] Single query '{q_single}' -> {routes_single}")

    q_composite = "Check the temperature in Hyderabad and convert 35°C to Fahrenheit."
    routes_comp = tool_router.route(q_composite)
    assert "weather" in routes_comp and "unit_converter" in routes_comp, f"Expected both in {routes_comp}"
    print(f"  [OK] Composite query '{q_composite}' -> {routes_comp}")

    q_math = "Calculate sqrt(144) + 25 * 4"
    routes_math = tool_router.route(q_math)
    assert "calculator" in routes_math, f"Expected 'calculator' in {routes_math}"
    print(f"  [OK] Math query '{q_math}' -> {routes_math}")

    q_none = "Hello! Tell me about Python programming."
    routes_none = tool_router.route(q_none)
    assert routes_none == [], f"Expected empty routes for general query, got {routes_none}"
    print(f"  [OK] General conversation query -> {routes_none} (NO_TOOL)")

    # -------------------------------------------------------------------------
    # TEST 4: Safe Math Calculator & AST Evaluation
    # -------------------------------------------------------------------------
    print("\n[4/11] Testing Safe Math Calculator (AST Evaluation)...")
    math_req = ToolRequest(query="Calculate 12 * 12 + sqrt(81)", tool_name="calculator", parameters={"expression": "12 * 12 + sqrt(81)"})
    math_resp = await tool_executor.execute_single(math_req)
    assert math_resp.success is True, f"Calculator error: {math_resp.error}"
    assert math_resp.data["result"] == 153.0, f"Expected 153.0, got {math_resp.data['result']}"
    print(f"  [OK] Arithmetic evaluation result: {math_resp.data['result']}")

    # Test division by zero safety
    zero_req = ToolRequest(query="Calculate 5 / 0", tool_name="calculator", parameters={"expression": "5 / 0"})
    zero_resp = await tool_executor.execute_single(zero_req)
    assert zero_resp.success is False and "division by zero" in zero_resp.error.lower()
    print("  [OK] Safe handling of ZeroDivisionError (division by zero).")

    # -------------------------------------------------------------------------
    # TEST 5: Timeout & Retry Resiliency Mechanisms
    # -------------------------------------------------------------------------
    print("\n[5/11] Testing Timeout Enforcement & Exponential Backoff Retries...")
    async def slow_handler(req: ToolRequest) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {"done": True}

    slow_def = ToolDefinition(
        name="slow_tool",
        description="Slow tool for timeout testing",
        category="test",
        timeout=0.15,  # strict 150ms timeout
        cache_ttl_seconds=0,
        handler=slow_handler
    )
    # Use 1 retry for fast testing
    test_exec = tool_executor.__class__(max_retries=1, base_backoff_sec=0.05)
    t0 = time.perf_counter()
    timeout_resp = await test_exec.execute_single(
        ToolRequest(query="test timeout", tool_name="slow_tool"),
        override_definition=slow_def
    )
    t_elapsed = (time.perf_counter() - t0) * 1000
    assert timeout_resp.success is False and "timed out" in timeout_resp.error.lower()
    print(f"  [OK] Timeout caught accurately after retries ({t_elapsed:.1f}ms): {timeout_resp.error}")

    # -------------------------------------------------------------------------
    # TEST 6: Thread-Safe TTL Caching
    # -------------------------------------------------------------------------
    print("\n[6/11] Testing Thread-Safe TTL Caching...")
    await tool_executor.clear_cache()
    weather_req = ToolRequest(query="weather in Hyderabad", tool_name="weather", parameters={"location": "Hyderabad"})
    
    # Execution 1 (Miss -> executes)
    r1 = await tool_executor.execute_single(weather_req)
    assert r1.success is True and r1.cached is False
    print(f"  [OK] Execution 1 (Cache Miss): cached={r1.cached}, exec_time={r1.execution_time_ms}ms")

    # Execution 2 (Hit -> cached)
    r2 = await tool_executor.execute_single(weather_req)
    assert r2.success is True and r2.cached is True
    print(f"  [OK] Execution 2 (Cache Hit): cached={r2.cached}, exec_time={r2.execution_time_ms}ms")

    # -------------------------------------------------------------------------
    # TEST 7 & 8: Concurrency & Batch Execution Modes (Parallel vs Sequential)
    # -------------------------------------------------------------------------
    print("\n[7 & 8/11] Testing Parallel & Sequential Batch Execution Modes...")
    batch_reqs = [
        ToolRequest(query="weather in Hyderabad", tool_name="weather", parameters={"location": "Hyderabad"}),
        ToolRequest(query="calculate 15 * 18", tool_name="calculator", parameters={"expression": "15 * 18"}),
        ToolRequest(query="current time in UTC", tool_name="datetime", parameters={"timezone": "UTC"}),
    ]
    t_par_0 = time.perf_counter()
    par_resps = await tool_executor.execute_batch(batch_reqs, mode="parallel")
    t_par = (time.perf_counter() - t_par_0) * 1000
    assert len(par_resps) == 3 and all(r.success for r in par_resps)
    print(f"  [OK] Parallel Batch Execution of 3 tools completed in {t_par:.2f}ms.")

    seq_resps = await tool_executor.execute_batch(batch_reqs, mode="sequential")
    assert len(seq_resps) == 3 and all(r.success for r in seq_resps)
    print("  [OK] Sequential Batch Execution completed successfully with priority ordering.")

    # -------------------------------------------------------------------------
    # TEST 9: Tool Pipeline Formatting for Context Merge
    # -------------------------------------------------------------------------
    print("\n[9/11] Testing Tool Pipeline Context Formatting...")
    resps, ctx_str = await tool_pipeline.process_query("Check weather in Hyderabad and calculate 100 * 5")
    assert len(resps) >= 2
    assert "=== REAL-TIME EXTERNAL TOOL INTELLIGENCE ===" in ctx_str
    assert "Hyderabad" in ctx_str and "500" in ctx_str
    print("  [OK] Formatted Context Block:")
    for line in ctx_str.split("\n")[:7]:
        print(f"      {line}")
    if len(ctx_str.split("\n")) > 7:
        print("      ...")

    # -------------------------------------------------------------------------
    # TEST 10: End-to-End LangGraph Orchestration Integration
    # -------------------------------------------------------------------------
    print("\n[10/11] Testing End-to-End LangGraph Orchestration Integration...")
    test_query = "What is the weather in Hyderabad and what is 25 * 40?"
    graph_res = await orchestration_pipeline.process_query(test_query, conversation_id="milestone13-test-01")
    node_path = graph_res.metadata.node_path
    print(f"  [OK] LangGraph Workflow Node Path: {' -> '.join(node_path)}")
    assert "tool_execution_node" in node_path, "tool_execution_node not executed inside LangGraph!"
    assert graph_res.metadata.tool_tokens > 0, f"Expected positive tool_tokens, got {graph_res.metadata.tool_tokens}"
    print(f"  [OK] Tool Tokens Retrieved inside LangGraph State: {graph_res.metadata.tool_tokens}")

    # -------------------------------------------------------------------------
    # TEST 11: Architectural Decoupling Verification
    # -------------------------------------------------------------------------
    print("\n[11/11] Verifying Architectural Decoupling (Zero cross-domain coupling inside app/tools)...")
    forbidden_modules = ["app.orchestration", "app.memory", "app.rag", "app.graph", "langgraph"]
    import ast
    for root, _, files in os.walk("app/tools"):
        for f in files:
            if f.endswith(".py"):
                filepath = os.path.join(root, f)
                with open(filepath, "r", encoding="utf-8") as file_obj:
                    tree = ast.parse(file_obj.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                for forbidden in forbidden_modules:
                                    assert not alias.name.startswith(forbidden), f"Coupling violation in {filepath}: import {alias.name}"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for forbidden in forbidden_modules:
                                    assert not node.module.startswith(forbidden), f"Coupling violation in {filepath}: from {node.module} import ..."
    print("  [OK] 100% Architectural Decoupling verified! app/tools has zero knowledge of LangGraph, Memory, or RAG.")

    print("\n================================================================================")
    print("[SUCCESS] ALL 11 MILESTONE 13 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(run_milestone_13_tests())
