# utils/interview_memory.py
"""
Conversational Clinical Memory System
--------------------------------------
Manages structured interview state, memory extraction, question
deduplication via embeddings, and intelligent termination logic.

Designed to slot into the existing LangGraph / FastAPI architecture
with minimal disruption.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Embedding model (loaded once at module import)
# ---------------------------------------------------------------------------
# _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
_EMBED_MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Simple in-memory embedding cache to avoid recomputing embeddings for identical texts
_embed_cache = {}

# Cosine similarity threshold above which two questions are "the same"
DEDUP_THRESHOLD: float = 0.70

# Hard upper bound on interview turns (safety net against infinite loops)
MAX_TURNS: int = 12


# ---------------------------------------------------------------------------
# Structured Interview State
# ---------------------------------------------------------------------------

def make_interview_state() -> Dict[str, Any]:
    """
    Return a fresh, empty interview state dict.

    Fields
    ------
    known_facts            : dict  – extracted clinical facts (dynamic keys)
    unavailable_information: list  – items the patient cannot / will not provide
    questions_asked        : list  – plain-text history of every asked question
    asked_embeddings       : list  – numpy arrays (stored as lists for JSON compat)
    confidence_score       : float – 0.0-1.0 running estimate of info completeness
    conversation_stage     : str   – "gathering" | "refining" | "finalizing"
    turn_count             : int   – number of completed Q-A turns
    """
    return {
        "known_facts": {},
        "unavailable_information": [],
        "questions_asked": [],
        "pending_questions": [],
        "patient_replies": [],
        "asked_embeddings": [],   # List[List[float]]
        "confidence_score": 0.0,
        "conversation_stage": "gathering",
        "turn_count": 0,
    }


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def embed_text(text: str) -> List[float]:
    """Return a unit-norm embedding for *text* as a plain Python list.
    Uses an in-memory cache to avoid repeated expensive calls for the same text.
    """
    if text in _embed_cache:
        return _embed_cache[text]
    vec = _EMBED_MODEL.encode(text, normalize_embeddings=True)
    arr = vec.tolist()
    _embed_cache[text] = arr
    return arr


def clear_embedding_cache():
    """Clear the in-memory embedding cache."""
    _embed_cache.clear()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two pre-normalised vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot = float(np.dot(va, vb))
    # Vectors are already unit-normed, so dot product == cosine similarity.
    return dot


# ---------------------------------------------------------------------------
# Question deduplication
# ---------------------------------------------------------------------------

def is_duplicate_question(
    new_question: str,
    interview_state: Dict[str, Any],
    threshold: float = DEDUP_THRESHOLD,
) -> Tuple[bool, float]:
    """
    Return (is_duplicate, max_similarity_score).

    A question is a duplicate if its cosine similarity with any previously
    asked question exceeds *threshold* (default 0.70).

    What this catches (all-MiniLM-L6-v2 typical scores)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "How long have you had the fever?"  vs  "When did your fever start?"     → ~0.80 ✓
    "Do you have chest pain?"  vs  "Are you experiencing chest discomfort?"  → ~0.85 ✓
    "Are you taking medication?"  vs  "Do you take any medicines regularly?" → ~0.78 ✓

    What this does NOT catch (by design)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "Do you have blood reports?"  vs  "Can you upload your CBC results?"     → ~0.47 ✗
    Lexically distant medical synonyms score too low for this model.
    Those cases are handled by the LLM's own memory context prompt, which
    lists all previously asked questions and instructs the model not to
    repeat their intent.  The embedding check is a safety net for close
    paraphrases the LLM might miss; the LLM prompt is the primary guard.
    """
    past_embeddings: List[List[float]] = interview_state.get("asked_embeddings", [])
    if not past_embeddings:
        return False, 0.0

    new_emb = embed_text(new_question)
    max_sim = max(cosine_similarity(new_emb, past) for past in past_embeddings)
    return max_sim >= threshold, max_sim


def register_question(
    question: str,
    interview_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Add *question* to the interview state's question history and embedding store.
    Returns the *mutated* interview_state (also mutates in-place for convenience).
    """
    interview_state["questions_asked"].append(question)
    interview_state["asked_embeddings"].append(embed_text(question))
    return interview_state


# ---------------------------------------------------------------------------
# Confidence & stage helpers
# ---------------------------------------------------------------------------

def update_confidence(
    interview_state: Dict[str, Any],
    specialist_status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Heuristically update confidence_score and conversation_stage.
    """
    # 1. Reduced the weight per fact (from 0.15 to 0.10)
    # 2. Lowered the absolute cap for facts (from 0.75 to 0.60)
    n_facts = len(interview_state.get("known_facts", {}))
    score = min(n_facts * 0.10, 0.60)

    if specialist_status == "complete":
        # Increased the bonus so the score still hits 1.0 when the specialist explicitly concludes
        score = min(score + 0.40, 1.0)

    interview_state["confidence_score"] = round(score, 2)

    turn = interview_state.get("turn_count", 0)
    MIN_TURNS = 5  # The AI is now strictly forced to ask at least 5 questions

    # 3. Stage transitions now require the MIN_TURNS threshold to be met
    if specialist_status == "complete" or (score >= 0.60 and turn >= MIN_TURNS):
        interview_state["conversation_stage"] = "finalizing"
    elif turn >= 4 or score >= 0.40:
        interview_state["conversation_stage"] = "refining"
    else:
        interview_state["conversation_stage"] = "gathering"

    return interview_state


# ---------------------------------------------------------------------------
# Termination logic
# ---------------------------------------------------------------------------

def should_force_terminate(interview_state: Dict[str, Any]) -> bool:
    """
    Hard safety-net: force termination if we've exceeded MAX_TURNS.
    The LLM's own "complete / incomplete" judgement remains the primary
    stopping mechanism — this is a backend guard only.
    """
    return interview_state.get("turn_count", 0) >= MAX_TURNS


def build_memory_context_block(interview_state: Dict[str, Any]) -> str:
    """
    Serialise the interview state into a concise text block that is injected
    into every specialist / question-generation prompt.

    Keeps prompts informed without bloating context.
    """
    known = interview_state.get("known_facts", {})
    unavailable = interview_state.get("unavailable_information", [])
    questions = interview_state.get("questions_asked", [])
    patient_replies = interview_state.get("patient_replies", [])
    stage = interview_state.get("conversation_stage", "gathering")
    turns = interview_state.get("turn_count", 0)
    confidence = interview_state.get("confidence_score", 0.0)

    known_str = (
        "\n".join(f"  - {k}: {v}" for k, v in known.items())
        if known
        else "  (none yet)"
    )
    unavailable_str = (
        "\n".join(f"  - {i}" for i in unavailable) if unavailable else "  (none)"
    )
    questions_str = (
        "\n".join(f"  {idx+1}. {q}" for idx, q in enumerate(questions))
        if questions
        else "  (none yet)"
    )
    replies_str = (
        "\n".join(
            f"  {idx+1}. Q: {item.get('question', '')}\n     A: {item.get('reply', '')}"
            for idx, item in enumerate(patient_replies)
        )
        if patient_replies
        else "  (none yet)"
    )

    return f"""\
=== INTERVIEW MEMORY CONTEXT ===
Stage            : {stage}
Turn             : {turns} / {MAX_TURNS}
Confidence Score : {confidence:.0%}

Known Facts (already gathered):
{known_str}

Unavailable Information (patient CANNOT / WILL NOT provide — DO NOT ask again):
{unavailable_str}

Questions Already Asked (DO NOT ask semantically equivalent questions):
{questions_str}

Patient Replies (use these answers as gathered clinical information):
{replies_str}
================================="""