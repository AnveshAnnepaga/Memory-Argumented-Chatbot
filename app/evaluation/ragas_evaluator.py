import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("app.evaluation.ragas")

try:
    from ragas.metrics.collections import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from ragas.llms import LlmWrapper
    from datasets import Dataset
    _RAGAS_AVAILABLE = True
except ImportError:
    try:
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from ragas.llms import LlmWrapper
        from datasets import Dataset
        _RAGAS_AVAILABLE = True
    except ImportError:
        _RAGAS_AVAILABLE = False
        logger.info("RAGAS not installed; falling back to heuristic RAG metrics.")

try:
    from app.ai.llm.llm_manager import llm_manager
    _LLM_AVAILABLE = True
except Exception:
    _LLM_AVAILABLE = False


class RAGASEvaluator:
    """
    RAGAS (RAG Assessment) integration for evaluating RAG pipeline quality.
    Uses LLM-as-judge to compute faithfulness, answer_relevancy, context_precision,
    and context_recall. Falls back to heuristic metrics when RAGAS is unavailable.
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and _LLM_AVAILABLE
        if _RAGAS_AVAILABLE and self.use_llm:
            self._init_ragas_llm()

    def _init_ragas_llm(self):
        """Wraps the local LLM manager as a RAGAS-compatible LLM interface."""
        try:
            class LocalLlmWrapper(LlmWrapper):
                def generate(self, messages, **kwargs) -> str:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    try:
                        res = loop.run_until_complete(
                            llm_manager.generate(
                                messages=messages,
                                temperature=kwargs.get("temperature", 0.1),
                                max_tokens=kwargs.get("max_tokens", 512),
                            )
                        )
                    finally:
                        loop.close()
                    return (res.get("content") or "").strip()

                async def agenerate(self, messages, **kwargs) -> str:
                    res = await llm_manager.generate(
                        messages=messages,
                        temperature=kwargs.get("temperature", 0.1),
                        max_tokens=kwargs.get("max_tokens", 512),
                    )
                    return (res.get("content") or "").strip()

            llm_wrapper = LocalLlmWrapper()
            faithfulness.llm = llm_wrapper
            answer_relevancy.llm = llm_wrapper
            context_precision.llm = llm_wrapper
            context_recall.llm = llm_wrapper
        except Exception as e:
            logger.warning(f"Failed to init RAGAS LLM wrapper: {e}")
            self.use_llm = False

    async def evaluate(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Evaluates the RAG pipeline using RAGAS metrics.

        Args:
            queries: List of user questions.
            responses: List of LLM-generated answers.
            contexts: List of lists of retrieved context chunks per query.
            ground_truths: Optional list of reference answers for context_recall.

        Returns:
            Dict of metric_name -> score (0.0 to 1.0).
        """
        if not queries or not responses or not contexts:
            logger.warning("Empty input to RAGASEvaluator.evaluate")
            return {"faithfulness": 0.0, "answer_relevancy": 0.0, "context_precision": 0.0, "context_recall": 0.0}

        if _RAGAS_AVAILABLE and self.use_llm:
            try:
                return await self._evaluate_ragas(queries, responses, contexts, ground_truths)
            except Exception as e:
                logger.warning(f"RAGAS evaluation failed, falling back to heuristics: {e}")
        return self._evaluate_heuristic(queries, responses, contexts, ground_truths)

    async def _evaluate_ragas(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Runs actual RAGAS LLM-as-judge metrics."""
        data = {
            "question": queries,
            "answer": responses,
            "contexts": contexts,
        }
        if ground_truths:
            data["ground_truth"] = ground_truths

        dataset = Dataset.from_dict(data)

        # Compute metrics
        results = {}
        try:
            f_scores = await faithfulness.score(dataset)
            results["faithfulness"] = round(float(f_scores), 4)
        except Exception as e:
            logger.warning(f"faithfulness metric failed: {e}")
            results["faithfulness"] = 0.0

        try:
            ar_scores = await answer_relevancy.score(dataset)
            results["answer_relevancy"] = round(float(ar_scores), 4)
        except Exception as e:
            logger.warning(f"answer_relevancy metric failed: {e}")
            results["answer_relevancy"] = 0.0

        try:
            cp_scores = await context_precision.score(dataset)
            results["context_precision"] = round(float(cp_scores), 4)
        except Exception as e:
            logger.warning(f"context_precision metric failed: {e}")
            results["context_precision"] = 0.0

        if ground_truths:
            try:
                cr_scores = await context_recall.score(dataset)
                results["context_recall"] = round(float(cr_scores), 4)
            except Exception as e:
                logger.warning(f"context_recall metric failed: {e}")
                results["context_recall"] = 0.0

        logger.info(f"RAGAS evaluation complete: {results}")
        return results

    def _evaluate_heuristic(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Fallback heuristic evaluation when RAGAS is unavailable."""
        total = len(queries)
        if total == 0:
            return {"faithfulness": 0.0, "answer_relevancy": 0.0, "context_precision": 0.0, "context_recall": 0.0}

        from app.evaluation.metrics import calculate_groundedness, calculate_faithfulness

        faith_sum = 0.0
        relevancy_sum = 0.0
        prec_sum = 0.0
        recall_sum = 0.0

        for i in range(total):
            q = queries[i]
            r = responses[i]
            ctxs = contexts[i] if i < len(contexts) else []
            ctx_text = "\n\n".join(ctxs) if ctxs else ""

            import re
            q_words = set(re.findall(r"\w+", q.lower()))
            r_words = set(re.findall(r"\w+", r.lower()))

            faith_sum += calculate_faithfulness(r, ctx_text)
            relevancy_sum += len(r_words & q_words) / max(1, len(r_words))

            if ctxs:
                relevant = sum(1 for c in ctxs if len(q_words & set(re.findall(r"\w+", c.lower()))) >= 1)
                prec_sum += relevant / len(ctxs)
                if ground_truths and i < len(ground_truths):
                    gt_words = set(re.findall(r"\w+", ground_truths[i].lower()))
                    covered = sum(1 for c in ctxs if len(gt_words & set(re.findall(r"\w+", c.lower()))) >= 1)
                    recall_sum += covered / len(ctxs)
            else:
                prec_sum += 0.0

        results = {
            "faithfulness": round(faith_sum / total, 4),
            "answer_relevancy": round(relevancy_sum / total, 4),
            "context_precision": round(prec_sum / total, 4),
            "context_recall": round(recall_sum / total, 4) if ground_truths else 0.0,
        }
        logger.info(f"Heuristic RAG evaluation: {results}")
        return results


ragas_evaluator = RAGASEvaluator()
