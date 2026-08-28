"""
metrics.py

Configures the RAGAS evaluation metrics for ClinicaFlow.
"""

from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    ContextPrecision,
    LLMContextRecall,
)

from ragas.llms import LangchainLLMWrapper

try:
    from backend.utils.llm import llm
except ModuleNotFoundError:  # pragma: no cover - fallback for direct imports
    from utils.llm import llm


# ==========================================================
# Wrap the LangChain LLM for RAGAS
# ==========================================================

ragas_llm = LangchainLLMWrapper(llm)


# ==========================================================
# Metrics
# ==========================================================

RAGAS_METRICS = [
    Faithfulness(llm=ragas_llm),
    ResponseRelevancy(llm=ragas_llm),
    ContextPrecision(),
    LLMContextRecall(llm=ragas_llm),
]


def get_metrics():
    return RAGAS_METRICS