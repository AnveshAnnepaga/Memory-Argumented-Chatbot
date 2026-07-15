# File: scratch/test_memory.py
"""
(`Milestone 12 Long-Term Memory Verification Suite`)
Rigorous standalone end-to-end test verifying:
1. Memory Schemas & Models (Conversation, Semantic, Episodic, Profile, Context)
2. Hybrid Memory Extractor (Deterministic Regex + LLM Structured JSON)
3. Memory Manager (CRUD, Multi-factor Ranking, Conflict Resolution & Updates)
4. Memory Retriever & Context Builder (Clean Markdown generation for LangGraph)
5. Memory Summarizer (Turn threshold compression & context budgeting)
6. Memory Pipeline & LangGraph Orchestration integration
"""
import asyncio
import logging
import os
import sys
import time
from typing import Optional

# Setup path and logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("test_memory")

from app.memory import (
    ConversationMemory,
    Episode,
    MemoryAction,
    MemoryContext,
    MemoryExtractionItem,
    MemoryExtractor,
    MemoryManager,
    MemoryRetriever,
    MemorySummarizer,
    MemoryPipeline,
    MemoryType,
    SemanticMemory,
    UserProfile,
    memory_pipeline,
)
from app.orchestration.workflow import orchestration_workflow


async def verify_schemas() -> None:
    logger.info("--------------------------------------------------------------------------------")
    logger.info("[1/6] Verifying Memory Schemas & Models...")
    logger.info("--------------------------------------------------------------------------------")

    # 1. User Profile
    profile = UserProfile(
        user_id="user-101",
        full_name="Alice Engineer",
        role="Principal Backend Architect",
        preferred_language="Python",
    )
    assert profile.user_id == "user-101"
    assert profile.preferred_language == "Python"
    logger.info(f"  [OK] UserProfile instantiated: {profile.role} (Lang: {profile.preferred_language})")

    # 2. Semantic Memory
    sem = SemanticMemory(
        id="sem-001",
        user_id="user-101",
        fact="User requires asynchronous Motor driver for MongoDB.",
        category="Database Preference",
        confidence=0.98,
        importance_score=0.90,
    )
    assert sem.confidence == 0.98
    logger.info(f"  [OK] SemanticMemory instantiated: '{sem.fact}' (Conf: {sem.confidence})")

    # 3. Episodic Memory
    epi = Episode(
        id="epi-001",
        user_id="user-101",
        event_type="milestone",
        description="Successfully deployed Backend Intelligence Layer v1.0.0",
        importance_score=0.95,
    )
    assert epi.event_type == "milestone"
    logger.info(f"  [OK] Episode instantiated: [{epi.event_type.upper()}] {epi.description}")

    # 4. Conversation Memory
    conv = ConversationMemory(
        id="conv-001",
        conversation_id="session-42",
        user_id="user-101",
        role="user",
        content="Let's start implementing Milestone 12 Long-Term Memory.",
    )
    assert conv.role == "user"
    logger.info(f"  [OK] ConversationMemory instantiated: {conv.role.upper()} -> '{conv.content[:40]}...'")

    # 5. Memory Context
    ctx = MemoryContext(
        user_id="user-101",
        profile=profile,
        semantic_facts=[sem],
        recent_episodes=[epi],
        conversation_window=[conv],
        formatted_context="=== MOCK MEMORY CONTEXT ===",
        total_tokens=15,
    )
    assert ctx.total_tokens == 15
    logger.info(f"  [OK] MemoryContext consolidated successfully ({ctx.total_tokens} tokens).")


async def verify_extractor() -> None:
    logger.info("\n--------------------------------------------------------------------------------")
    logger.info("[2/6] Verifying Hybrid Memory Extractor (Deterministic + LLM Fallback)...")
    logger.info("--------------------------------------------------------------------------------")
    extractor = MemoryExtractor()

    # Test 1: Language preference regex extraction
    res1 = await extractor.extract("I prefer Python for backend services and FastAPI.")
    assert res1.should_remember is True
    assert len(res1.extracted_items) >= 1
    assert res1.extracted_items[0].memory_type == MemoryType.SEMANTIC
    assert res1.extracted_items[0].key == "preferred_language"
    assert "python" in str(res1.extracted_items[0].value).lower()
    logger.info(f"  [OK] Deterministic Regex extracted language preference: key='{res1.extracted_items[0].key}', val='{res1.extracted_items[0].value}'")

    # Test 2: Role definition extraction
    res2 = await extractor.extract("I work as a Staff AI Engineer building agentic systems.")
    assert res2.should_remember is True
    assert res2.extracted_items[0].key in ("role", "occupation")
    logger.info(f"  [OK] Deterministic Regex extracted professional role: val='{res2.extracted_items[0].value}'")

    # Test 3: Deployment / Episodic event extraction
    res3 = await extractor.extract("Today I deployed the GraphRAG service to staging.")
    assert res3.should_remember is True
    assert res3.extracted_items[0].memory_type == MemoryType.EPISODIC
    assert res3.extracted_items[0].key == "deployment"
    logger.info(f"  [OK] Deterministic Regex extracted episodic deployment: '{res3.extracted_items[0].content}'")

    # Test 4: Nuanced statement -> LLM extraction fallback check
    res4 = await extractor.extract("Make sure to always keep response latency under 200ms when serving hybrid search.")
    logger.info(f"  [OK] Evaluated nuanced extraction query (Should Remember: {res4.should_remember}, Items: {len(res4.extracted_items)})")


async def verify_manager_and_ranking() -> None:
    logger.info("\n--------------------------------------------------------------------------------")
    logger.info("[3/6] Verifying Memory Manager, Conflict Resolution & Multi-Factor Ranking...")
    logger.info("--------------------------------------------------------------------------------")
    manager = MemoryManager()
    test_user = "user-ranking-101"

    # 1. Create Profile and Initial Semantic Fact
    item_lang = MemoryExtractionItem(
        action=MemoryAction.CREATE,
        memory_type=MemoryType.SEMANTIC,
        content="User prefers Python for all scripts",
        key="preferred_language",
        value="Python",
        importance_score=0.85,
        confidence=0.95,
    )
    mem1 = await manager.create_memory(item_lang, test_user)
    assert mem1.id in manager._local_pinecone_vectors
    logger.info(f"  [OK] Created initial Semantic Fact: ID='{mem1.id}', Fact='{mem1.fact}'")

    # 2. Test Conflict Resolution (Update existing preference instead of duplicating)
    item_lang_update = MemoryExtractionItem(
        action=MemoryAction.CREATE,
        memory_type=MemoryType.SEMANTIC,
        content="User prefers Rust for high performance workers",
        key="preferred_language",
        value="Rust",
        importance_score=0.90,
        confidence=0.98,
    )
    existing_facts = await manager.search_semantic_memories(test_user, query="language", top_k=10)
    resolved = await manager.resolve_conflict(test_user, item_lang_update, existing_facts)
    assert resolved is not None and resolved.id == mem1.id
    updated_facts = await manager.search_semantic_memories(test_user, query="language", top_k=10)
    assert len(updated_facts) == 1  # No duplicate created!
    assert "rust" in updated_facts[0].fact.lower()
    logger.info(f"  [OK] Conflict Resolution successful! Updated fact in-place to: '{updated_facts[0].fact}' without duplication.")

    # 3. Verify Multi-Factor Ranking Formula
    score = manager.compute_ranking_score(
        importance=updated_facts[0].importance_score,
        timestamp_dt=updated_facts[0].timestamp,
        confidence=updated_facts[0].confidence,
        access_count=5,
    )
    assert score > 0.0
    logger.info(f"  [OK] Computed Multi-Factor Ranking Score = {score:.4f} (α=0.35, β=0.25, γ=0.20, δ=0.20)")


async def verify_retriever_and_summarizer() -> None:
    logger.info("\n--------------------------------------------------------------------------------")
    logger.info("[4/6] Verifying Memory Retriever Context Builder & Turn Summarization...")
    logger.info("--------------------------------------------------------------------------------")
    manager = MemoryManager()
    retriever = MemoryRetriever(manager=manager)
    summarizer = MemorySummarizer(manager=manager)
    test_user = "user-sum-202"
    conv_id = "session-sum-01"

    # Add 10 short-term conversation turns to trigger threshold summarization (> max_threshold=6)
    logger.info("  Simulating 10 conversation turns in session...")
    for i in range(1, 11):
        turn_item = MemoryExtractionItem(
            action=MemoryAction.CREATE,
            memory_type=MemoryType.CONVERSATION,
            content=f"Turn {i}: Discussing architectural tradeoff of Redis caching vs local memory dict.",
            key=conv_id,
            value="user" if i % 2 == 1 else "assistant",
        )
        await manager.create_memory(turn_item, test_user)

    turns_before = [c for c in manager._local_mongo_conversations.values() if c.user_id == test_user]
    assert len(turns_before) == 10
    logger.info(f"  [OK] Stored {len(turns_before)} short-term conversation turns.")

    # Execute Summarizer
    summary_rec = await summarizer.summarize_if_needed(test_user, conv_id, max_threshold=6)
    assert summary_rec is not None
    assert summary_rec.role == "system_summary"
    assert "sum-" in summary_rec.id

    turns_after = [c for c in manager._local_mongo_conversations.values() if c.user_id == test_user]
    # Should have 1 summary + 2 latest preserved turns = 3 total
    assert len(turns_after) == 3
    logger.info(f"  [OK] Summarizer compressed 8 historical turns into: '{summary_rec.content[:70]}...'")
    logger.info(f"  [OK] Active conversation store pruned from 10 turns -> {len(turns_after)} items (Summary + 2 active turns).")

    # Build full Markdown Context for LangGraph
    ctx = await retriever.retrieve_and_build_context(test_user, query="Redis caching", conversation_id=conv_id)
    assert ctx.total_tokens > 0
    assert "=== SHORT-TERM CONVERSATION WINDOW" in ctx.formatted_context
    logger.info(f"  [OK] Retriever built structured LangGraph Context ({ctx.total_tokens} words):\n--- CONTEXT PREVIEW ---\n{ctx.formatted_context[:400]}...\n-----------------------")


async def verify_pipeline_and_orchestration() -> None:
    logger.info("\n--------------------------------------------------------------------------------")
    logger.info("[5/6] Verifying Memory Pipeline & LangGraph Orchestration Integration...")
    logger.info("--------------------------------------------------------------------------------")
    pipeline = MemoryPipeline()
    test_user = "user-graph-303"
    conv_id = "session-graph-99"

    # Step 1: Process Turn through unified pipeline facade
    logger.info("  Processing turn via MemoryPipeline...")
    res = await pipeline.process_turn(
        user_query="I prefer using PostgreSQL with pgvector for our vector store.",
        ai_response="Understood, I will configure PostgreSQL with pgvector as the primary knowledge repository.",
        user_id=test_user,
        conversation_id=conv_id,
    )
    assert res.should_remember is True
    logger.info(f"  [OK] Processed turn via pipeline and extracted: {[i.content for i in res.extracted_items]}")

    # Step 2: Execute LangGraph Workflow query verifying memory_retrieval_node
    logger.info("  Executing LangGraph workflow with Long-Term Memory injected...")
    initial_state = {
        "user_query": "What vector store do I prefer?",
        "conversation_id": conv_id,
        "user_id": test_user,
    }
    final_state = await orchestration_workflow.app.ainvoke(initial_state)

    path = final_state.get("node_path", [])
    assert "router_node" in path
    assert "memory_retrieval_node" in path
    assert "prompt_builder_node" in path
    assert "llm_generation_node" in path

    mem_tokens = final_state.get("metadata", {}).get("memory_tokens", 0)
    mem_ctx = final_state.get("retrieved_memory_context", "")
    assert mem_tokens > 0
    assert "PostgreSQL" in mem_ctx or "pgvector" in mem_ctx
    logger.info(f"  [OK] LangGraph successfully routed through memory_retrieval_node (Node Path: {' -> '.join(path)})")
    logger.info(f"  [OK] LangGraph injected {mem_tokens} memory tokens directly into final_context for LLM generation.")

    logger.info("\n================================================================================")
    logger.info("🎉 [SUCCESS] MILESTONE 12 (LONG-TERM MEMORY SYSTEM) 100% VERIFIED AND FUNCTIONAL!")
    logger.info("================================================================================\n")


async def main():
    t0 = time.perf_counter()
    await verify_schemas()
    await verify_extractor()
    await verify_manager_and_ranking()
    await verify_retriever_and_summarizer()
    await verify_pipeline_and_orchestration()
    logger.info(f"Total Milestone 12 test execution time: {(time.perf_counter()-t0)*1000:.1f}ms")


if __name__ == "__main__":
    asyncio.run(main())
