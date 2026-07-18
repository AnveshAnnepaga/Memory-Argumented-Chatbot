"""
RAGAS Evaluation Script for the RAG Pipeline.
Runs RAGAS LLM-as-judge metrics (faithfulness, answer_relevancy,
context_precision, context_recall) on the RAG pipeline output.

Usage:
    python scripts/ragas_evaluate.py                     # Uses sample data
    python scripts/ragas_evaluate.py --live               # Uses live pipeline
    python scripts/ragas_evaluate.py --output results.json # Save results
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ragas_evaluate")

# Sample test queries for RAG evaluation
SAMPLE_QUERIES = [
    {
        "query": "What are the core features of FastAPI?",
        "response": "FastAPI is a modern web framework that features automatic Swagger UI docs and asynchronous dependency injection.",
        "contexts": [
            "FastAPI is a modern web framework built on Pydantic and Starlette. It provides automatic Swagger documentation and dependency injection."
        ],
        "ground_truth": "FastAPI is a modern Python web framework with automatic OpenAPI docs, async support, and dependency injection."
    },
    {
        "query": "How does Hybrid RAG work in this system?",
        "response": "Hybrid RAG combines dense vector search from Pinecone with sparse BM25 retrieval for balanced precision and recall.",
        "contexts": [
            "Hybrid RAG combines dense Pinecone vectors and BM25 sparse index for retrieval. Dense search captures semantic similarity while sparse search ensures keyword precision."
        ],
        "ground_truth": "The Hybrid RAG system combines dense vector search (Pinecone) with sparse keyword search (BM25) for optimal retrieval."
    },
    {
        "query": "What is GraphRAG used for?",
        "response": "GraphRAG extracts entity relationships stored in Neo4j for multi-hop reasoning across connected concepts.",
        "contexts": [
            "GraphRAG extracts entity relationships stored in Neo4j. It enables multi-hop reasoning across connected concepts and structural knowledge traversal."
        ],
        "ground_truth": "GraphRAG is used for extracting and querying entity relationships in Neo4j to enable multi-hop reasoning."
    },
    {
        "query": "What databases are used in this system?",
        "response": "The system uses Pinecone for vector storage, Neo4j for graph storage, and PostgreSQL for relational data.",
        "contexts": [
            "Pinecone is used for vector similarity search and dense retrieval. Neo4j stores knowledge graph entities and relationships. PostgreSQL handles relational data persistence."
        ],
        "ground_truth": "The system uses Pinecone (vector DB), Neo4j (graph DB), and PostgreSQL (relational DB)."
    },
    {
        "query": "Explain the memory system architecture.",
        "response": "The memory system has short-term conversation memory, semantic memory for user facts, episodic memory for significant events, and user profiles.",
        "contexts": [
            "The memory system architecture includes: conversation memory (short-term turns), semantic memory (long-term user facts), episodic memory (significant events), and user profiles (structured preferences)."
        ],
        "ground_truth": "The memory system consists of conversation memory, semantic memory, episodic memory, and user profiles."
    },
]


async def evaluate_with_ragas(
    queries: List[str],
    responses: List[str],
    contexts: List[List[str]],
    ground_truths: Optional[List[str]] = None,
    use_live_llm: bool = True,
) -> Dict[str, Any]:
    """Run RAGAS evaluation on the given data."""
    from app.evaluation.ragas_evaluator import ragas_evaluator, _RAGAS_AVAILABLE

    if not _RAGAS_AVAILABLE:
        logger.error("RAGAS is not installed. Install it with: pip install ragas")
        return {"error": "RAGAS not available", "installed": False}

    logger.info(f"Running RAGAS evaluation on {len(queries)} samples (LLM-as-judge: {use_live_llm})...")
    results = await ragas_evaluator.evaluate(
        queries=queries,
        responses=responses,
        contexts=contexts,
        ground_truths=ground_truths,
    )

    logger.info(f"RAGAS evaluation complete: {json.dumps(results, indent=2)}")
    return results


async def evaluate_live_pipeline(test_queries: List[str]) -> Dict[str, Any]:
    """Run queries through the live orchestration pipeline and evaluate with RAGAS."""
    from app.orchestration.pipeline import orchestration_pipeline
    from app.evaluation.ragas_evaluator import ragas_evaluator, _RAGAS_AVAILABLE

    if not _RAGAS_AVAILABLE:
        return {"error": "RAGAS not available"}

    logger.info(f"Running {len(test_queries)} queries through live pipeline...")
    queries = []
    responses = []
    contexts = []
    route_info = []

    for i, q in enumerate(test_queries):
        logger.info(f"Query {i+1}/{len(test_queries)}: {q[:60]}...")
        try:
            result = await orchestration_pipeline.process_query(
                user_query=q,
                conversation_id="ragas-eval",
                user_id="ragas-evaluator",
            )
            queries.append(q)
            responses.append(result.response)
            rag_ctx = result.prompt_context.rag_context if result.prompt_context else ""
            contexts.append([rag_ctx] if rag_ctx else ["No context retrieved"])
            route_info.append(result.router_decision.route.value if result.router_decision else "UNKNOWN")
            logger.info(f"  Route: {route_info[-1]}, Resp: {result.response[:60]}...")
        except Exception as e:
            logger.error(f"  Query {i+1} failed: {e}")
            queries.append(q)
            responses.append(f"Error: {e}")
            contexts.append(["Error"])
            route_info.append("ERROR")

    logger.info("Running RAGAS evaluation on live pipeline results...")
    ragas_results = await ragas_evaluator.evaluate(
        queries=queries,
        responses=responses,
        contexts=contexts,
    )

    return {
        "pipeline_results": [
            {"query": q, "response": r, "route": r_info}
            for q, r, r_info in zip(queries, responses, route_info)
        ],
        "ragas_metrics": ragas_results,
        "sample_count": len(queries),
    }


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="RAGAS Evaluation for RAG Pipeline")
    parser.add_argument("--live", action="store_true", help="Run queries through live pipeline")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON file")
    parser.add_argument("--llm", action="store_true", default=True, help="Use LLM-as-judge (default: True)")
    args = parser.parse_args()

    if args.live:
        test_queries = [q["query"] for q in SAMPLE_QUERIES]
        results = await evaluate_live_pipeline(test_queries)
    else:
        queries = [q["query"] for q in SAMPLE_QUERIES]
        responses = [q["response"] for q in SAMPLE_QUERIES]
        contexts = [q["contexts"] for q in SAMPLE_QUERIES]
        ground_truths = [q["ground_truth"] for q in SAMPLE_QUERIES]

        results = {
            "sample_data": True,
            "sample_count": len(queries),
            "ragas_metrics": await evaluate_with_ragas(
                queries=queries,
                responses=responses,
                contexts=contexts,
                ground_truths=ground_truths,
                use_live_llm=args.llm,
            ),
        }

    # Print formatted results
    metrics = results.get("ragas_metrics", {})
    print("\n" + "=" * 60)
    print("  RAGAS EVALUATION RESULTS")
    print("=" * 60)
    if "error" in metrics:
        print(f"  ERROR: {metrics['error']}")
    else:
        for metric, score in metrics.items():
            bar_len = int(score * 40) if isinstance(score, (int, float)) else 0
            bar = "█" * bar_len + "░" * (40 - bar_len)
            print(f"  {metric:25s} {score:>8.4f}  |{bar}|")
    print("=" * 60)

    # Per-sample breakdown for live mode
    if "pipeline_results" in results:
        print("\nPer-Query Breakdown:")
        for i, pr in enumerate(results["pipeline_results"]):
            print(f"  [{i+1}] Route: {pr['route']}")
            print(f"      Query:    {pr['query'][:80]}")
            print(f"      Response: {pr['response'][:80]}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
