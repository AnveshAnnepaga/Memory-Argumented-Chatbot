# File: app/tests/rag/test_ragas_evaluation.py
"""
RAGAS Evaluation Test Suite for RAG + LLM Answer Quality Assessment

Run with:
    python -m pytest app/tests/rag/test_ragas_evaluation.py -v -s

Tests both:
    1. RAG Retrieval Quality (context precision/recall)
    2. LLM Answer Quality (faithfulness, answer relevancy)
"""
import pytest
import pytest_asyncio
import asyncio
from typing import List, Dict, Any

from app.evaluation.ragas_evaluator import RAGASEvaluator
from app.rag.pipeline import rag_pipeline
from app.ai.llm.llm_manager import llm_manager
from app.domain.knowledge import Document


# Enable stub mode for fast testing (no external API calls)
from app.rag import embedder, hybrid_retriever
embedder.use_stub = True
if hasattr(hybrid_retriever, "reranker") and hasattr(hybrid_retriever.reranker, "use_stub"):
    hybrid_retriever.reranker.use_stub = True


class RAGASEvaluationSuite:
    """Complete RAGAS evaluation suite for testing RAG + LLM answers."""

    def __init__(self):
        self.evaluator = RAGASEvaluator(use_llm=True)
        self.test_dataset: List[Dict[str, str]] = [
            {
                "query": "What is the Python Global Interpreter Lock (GIL)?",
                "ground_truth": "The GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes simultaneously in CPython.",
            },
            {
                "query": "How does FastAPI dependency injection work?",
                "ground_truth": "FastAPI uses Pydantic models and Depends() for dependency injection, enabling clean database session injection, automatic OpenAPI validation, and parameter sharing.",
            },
            {
                "query": "What is hybrid RAG retrieval?",
                "ground_truth": "Hybrid RAG combines dense vector search (Pinecone) with sparse keyword search (BM25) using Reciprocal Rank Fusion for better retrieval results.",
            },
            {
                "query": "Explain LangGraph orchestration workflow.",
                "ground_truth": "LangGraph uses a StateGraph to orchestrate multiple AI components through conditional routing, enabling complex multi-step workflows with state management.",
            },
            {
                "query": "What is the Ebbinghaus forgetting curve?",
                "ground_truth": "The Ebbinghaus forgetting curve describes how information is lost over time without reinforcement, showing rapid initial loss followed by slower decline.",
            },
        ]
        self.namespace = "test-ragas-eval"

    async def setup_test_documents(self) -> None:
        """Index test documents for retrieval evaluation."""
        docs = [
            Document(
                id="doc-gil",
                source_id="Python Docs",
                title="Python GIL & Threads",
                content="The Python Global Interpreter Lock (GIL) is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes simultaneously. This means true multi-core parallelism requires subinterpreters or multiprocessing.",
                metadata={"category": "python", "url": "https://docs.python.org/threads"},
            ),
            Document(
                id="doc-fastapi",
                source_id="FastAPI Docs",
                title="FastAPI Dependency Injection",
                content="FastAPI's dependency injection system enables clean architecture through Pydantic models and the Depends() function. It supports database session injection, automatic OpenAPI schema validation using Pydantic, and parameter sharing across route handlers.",
                metadata={"category": "web", "url": "https://fastapi.tiangolo.com/di"},
            ),
            Document(
                id="doc-rag",
                source_id="RAG Paper",
                title="Hybrid RAG Pipeline",
                content="Hybrid RAG combines dense vector embeddings from Pinecone with sparse BM25 keyword search. The results are fused using Reciprocal Rank Fusion (RRF) to leverage the strengths of both retrieval methods for better overall performance.",
                metadata={"category": "ml", "url": "https://arxiv.org/rag"},
            ),
            Document(
                id="doc-langgraph",
                source_id="LangGraph Docs",
                title="LangGraph StateGraph",
                content="LangGraph provides a StateGraph framework for building coordinated multi-step AI workflows. It uses conditional edges to route execution between nodes, maintaining state throughout the workflow execution.",
                metadata={"category": "ai", "url": "https://langchain.dev/langgraph"},
            ),
            Document(
                id="doc-memory",
                source_id="Cognitive Science",
                title="Ebbinghaus Memory Model",
                content="The Ebbinghaus forgetting curve describes how information retention decreases over time without active reinforcement. Hermann Ebbinghaus discovered that memory retention follows a logarithmic decay pattern.",
                metadata={"category": "cognitive", "url": "https://memory.science/forgetting"},
            ),
        ]
        await rag_pipeline.index_documents(docs, namespace=self.namespace)

    async def retrieve_contexts(self, query: str) -> List[str]:
        """Retrieve contexts for a query using the RAG pipeline."""
        ctx = await rag_pipeline.retrieve_context(
            query=query,
            top_k=3,
            namespace=self.namespace,
        )
        return [chunk.text for chunk in ctx.retrieved_chunks]

    async def generate_answer(self, query: str, contexts: List[str]) -> str:
        """Generate an answer using the LLM with retrieved contexts."""
        context_text = "\n\n".join([f"[Context {i+1}]: {c}" for i, c in enumerate(contexts)])
        prompt = f"""Answer the question based ONLY on the provided contexts.

Contexts:
{context_text}

Question: {query}

Answer:"""

        result = await llm_manager.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
        )
        return result.get("content", "").strip()

    async def run_full_evaluation(self) -> Dict[str, Any]:
        """
        Run complete RAGAS evaluation:
        1. Retrieve contexts for each test query
        2. Generate answers using LLM
        3. Evaluate with RAGAS metrics
        """
        queries = []
        responses = []
        contexts = []
        ground_truths = []

        for item in self.test_dataset:
            query = item["query"]
            gt = item["ground_truth"]

            ctx_list = await self.retrieve_contexts(query)
            answer = await self.generate_answer(query, ctx_list)

            queries.append(query)
            responses.append(answer)
            contexts.append(ctx_list)
            ground_truths.append(gt)

            print(f"\n[Query] {query}")
            print(f"[Contexts] {len(ctx_list)} retrieved")
            print(f"[Generated Answer] {answer[:100]}...")

        print("\n" + "="*60)
        print("Running RAGAS Evaluation...")
        print("="*60)

        metrics = await self.evaluator.evaluate(
            queries=queries,
            responses=responses,
            contexts=contexts,
            ground_truths=ground_truths,
        )

        return {
            "metrics": metrics,
            "details": {
                "queries": queries,
                "responses": responses,
                "contexts": contexts,
                "ground_truths": ground_truths,
            }
        }


@pytest_asyncio.fixture(scope="module")
async def eval_suite():
    """Setup evaluation suite with indexed documents."""
    suite = RAGASEvaluationSuite()
    await suite.setup_test_documents()
    yield suite


@pytest.mark.asyncio
async def test_ragas_retrieval_and_answer_evaluation(eval_suite):
    """Test full RAGAS evaluation pipeline for RAG + LLM answers."""
    results = await eval_suite.run_full_evaluation()

    metrics = results["metrics"]
    print("\n" + "="*60)
    print("RAGAS EVALUATION RESULTS")
    print("="*60)
    print(f"  Faithfulness:      {metrics.get('faithfulness', 'N/A')}")
    print(f"  Answer Relevancy:  {metrics.get('answer_relevancy', 'N/A')}")
    print(f"  Context Precision: {metrics.get('context_precision', 'N/A')}")
    print(f"  Context Recall:    {metrics.get('context_recall', 'N/A')}")

    assert "faithfulness" in metrics
    assert "answer_relevancy" in metrics
    assert "context_precision" in metrics
    assert "context_recall" in metrics

    for key, value in metrics.items():
        assert 0.0 <= value <= 1.0, f"{key} score {value} out of range [0, 1]"


@pytest.mark.asyncio
async def test_individual_query_evaluation(eval_suite):
    """Test evaluation of a single query for debugging."""
    query = "What is the Python Global Interpreter Lock?"
    ground_truth = "The GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes simultaneously in CPython."

    ctx_list = await eval_suite.retrieve_contexts(query)
    answer = await eval_suite.generate_answer(query, ctx_list)

    print(f"\n[Query] {query}")
    print(f"[Contexts Retrieved] {len(ctx_list)}")
    for i, ctx in enumerate(ctx_list):
        print(f"  Context {i+1}: {ctx[:80]}...")
    print(f"[Generated Answer] {answer}")

    metrics = await eval_suite.evaluator.evaluate(
        queries=[query],
        responses=[answer],
        contexts=[ctx_list],
        ground_truths=[ground_truth],
    )

    print(f"\n[Metrics] {metrics}")
    assert "faithfulness" in metrics


@pytest.mark.asyncio
async def test_ragas_without_llm_fallback():
    """Test RAGAS evaluator fallback when LLM is not available."""
    evaluator = RAGASEvaluator(use_llm=False)

    queries = ["What is Python?", "How does FastAPI work?"]
    responses = [
        "Python is a programming language.",
        "FastAPI is a web framework.",
    ]
    contexts = [
        ["Python is a high-level programming language.", "Python supports async."],
        ["FastAPI is a modern web framework.", "FastAPI supports dependency injection."],
    ]
    ground_truths = [
        "Python is a high-level, general-purpose programming language.",
        "FastAPI is a modern Python web framework with async support.",
    ]

    metrics = await evaluator.evaluate(
        queries=queries,
        responses=responses,
        contexts=contexts,
        ground_truths=ground_truths,
    )

    print(f"\n[Fallback Metrics] {metrics}")
    assert "faithfulness" in metrics
    assert all(0.0 <= v <= 1.0 for v in metrics.values())


if __name__ == "__main__":
    async def run_manual_evaluation():
        """Run manual evaluation without pytest."""
        suite = RAGASEvaluationSuite()
        await suite.setup_test_documents()
        results = await suite.run_full_evaluation()

        print("\n" + "="*60)
        print("FINAL RAGAS EVALUATION REPORT")
        print("="*60)
        for key, value in results["metrics"].items():
            print(f"  {key}: {value}")

        return results

    asyncio.run(run_manual_evaluation())