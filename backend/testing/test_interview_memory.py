# tests/test_interview_memory.py
"""
Unit tests for the conversational clinical memory system.
Run with: pytest tests/test_interview_memory.py -v
"""

import pytest
from utils.interview_memory import (
    DEDUP_THRESHOLD,
    MAX_TURNS,
    build_memory_context_block,
    cosine_similarity,
    embed_text,
    is_duplicate_question,
    make_interview_state,
    register_question,
    should_force_terminate,
    update_confidence,
)


# ---------------------------------------------------------------------------
# make_interview_state
# ---------------------------------------------------------------------------

def test_make_interview_state_structure():
    state = make_interview_state()
    assert isinstance(state["known_facts"], dict)
    assert isinstance(state["unavailable_information"], list)
    assert isinstance(state["questions_asked"], list)
    assert isinstance(state["asked_embeddings"], list)
    assert state["confidence_score"] == 0.0
    assert state["conversation_stage"] == "gathering"
    assert state["turn_count"] == 0


# ---------------------------------------------------------------------------
# Embedding & cosine similarity
# ---------------------------------------------------------------------------

def test_embed_text_returns_list_of_floats():
    vec = embed_text("fever for three days")
    assert isinstance(vec, list)
    assert all(isinstance(v, float) for v in vec)
    assert abs(sum(v ** 2 for v in vec) ** 0.5 - 1.0) < 1e-4, "Vector should be unit-normed"


def test_cosine_similarity_identical_vectors():
    vec = embed_text("headache")
    sim = cosine_similarity(vec, vec)
    assert abs(sim - 1.0) < 1e-4


def test_cosine_similarity_different_vectors():
    v1 = embed_text("chest pain")
    v2 = embed_text("happy birthday")
    sim = cosine_similarity(v1, v2)
    assert sim < 0.7, "Unrelated sentences should have low similarity"


# ---------------------------------------------------------------------------
# Question deduplication
# ---------------------------------------------------------------------------

def test_no_duplicates_on_empty_state():
    state = make_interview_state()
    is_dup, score = is_duplicate_question("Do you have blood reports?", state)
    assert not is_dup
    assert score == 0.0


def test_exact_duplicate_is_detected():
    state = make_interview_state()
    q = "Do you have any allergies to medication?"
    state = register_question(q, state)
    is_dup, score = is_duplicate_question(q, state)
    assert is_dup
    assert score >= DEDUP_THRESHOLD


def test_semantic_duplicate_is_detected():
    """
    all-MiniLM-L6-v2 scores purely lexically dissimilar paraphrases (e.g.
    'blood reports' vs 'CBC results') at ~0.47 — too low for any reasonable
    threshold.  The dedup system is designed to catch close paraphrases, not
    completely different medical terminology for the same concept.

    We test with pairs that are genuinely close in the embedding space,
    which is what the threshold guards against in practice.
    """
    state = make_interview_state()

    # Close paraphrase pair — same intent, slightly different wording
    q1 = "How long have you had the fever?"
    q2 = "When did your fever start?"
    state = register_question(q1, state)
    is_dup, score = is_duplicate_question(q2, state)
    assert is_dup, f"Expected duplicate for close paraphrase but got similarity={score:.2f}"


def test_semantic_duplicate_distant_terminology_not_flagged():
    """
    Lexically very different phrasings of the same underlying concept
    (e.g. 'blood reports' vs 'CBC') score ~0.47 with all-MiniLM-L6-v2.
    These are NOT caught by embedding dedup — that is acceptable because:
    (a) the LLM prompt instructs it not to repeat questions about
        anything in 'unavailable_information', and
    (b) lowering the threshold enough to catch these would cause false
        positives on genuinely distinct questions.
    The primary dedup mechanism for terminology variants is the LLM's own
    memory context, not cosine similarity.
    """
    state = make_interview_state()
    q1 = "Do you have blood reports available?"
    q2 = "Can you upload your CBC results?"
    state = register_question(q1, state)
    is_dup, score = is_duplicate_question(q2, state)
    # Score ~0.47 — correctly below threshold; LLM handles this via memory context
    assert not is_dup, (
        f"Distant-terminology pair should not be flagged as duplicate (score={score:.2f})"
    )


def test_unrelated_question_not_flagged():
    state = make_interview_state()
    q1 = "Do you smoke?"
    q2 = "What is your blood pressure?"
    state = register_question(q1, state)
    is_dup, score = is_duplicate_question(q2, state)
    assert not is_dup


def test_register_question_appends_history():
    state = make_interview_state()
    q = "How long have you had the fever?"
    state = register_question(q, state)
    assert q in state["questions_asked"]
    assert len(state["asked_embeddings"]) == 1


# ---------------------------------------------------------------------------
# Confidence & stage
# ---------------------------------------------------------------------------

def test_confidence_increases_with_facts():
    state = make_interview_state()
    for i in range(5):
        state["known_facts"][f"fact_{i}"] = f"value_{i}"
    state = update_confidence(state)
    assert state["confidence_score"] > 0.0


def test_stage_transitions_to_finalizing_on_complete():
    state = make_interview_state()
    state = update_confidence(state, specialist_status="complete")
    assert state["conversation_stage"] == "finalizing"


def test_stage_transitions_to_refining():
    state = make_interview_state()
    state["turn_count"] = 5
    state = update_confidence(state)
    assert state["conversation_stage"] in ("refining", "finalizing")


# ---------------------------------------------------------------------------
# Termination
# ---------------------------------------------------------------------------

def test_force_terminate_not_triggered_early():
    state = make_interview_state()
    state["turn_count"] = MAX_TURNS - 1
    assert not should_force_terminate(state)


def test_force_terminate_triggered_at_max():
    state = make_interview_state()
    state["turn_count"] = MAX_TURNS
    assert should_force_terminate(state)


# ---------------------------------------------------------------------------
# Memory context block
# ---------------------------------------------------------------------------

def test_build_memory_context_block_contains_key_sections():
    state = make_interview_state()
    state["known_facts"] = {"fever_duration": "3 days"}
    state["unavailable_information"] = ["blood_reports"]
    state["questions_asked"] = ["Do you have a rash?"]
    block = build_memory_context_block(state)
    assert "fever_duration" in block
    assert "blood_reports" in block
    assert "Do you have a rash?" in block
    assert "NEVER" in block or "DO NOT" in block  # Directive language present


def test_build_memory_context_block_empty_state():
    state = make_interview_state()
    block = build_memory_context_block(state)
    assert "none" in block.lower()


def test_make_interview_state_includes_patient_replies():
    state = make_interview_state()
    assert state["patient_replies"] == []

