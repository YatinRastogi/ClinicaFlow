# utils/llm.py

from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import time
import json
import hashlib
import threading
import types

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# This LLM is for summarizing structured reports
lab_report_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    # model="meta-llama/llama-4-scout-17b-16e-instruct", # Fast and good for structured tasks
    model="openai/gpt-oss-20b", # Fast and good for structured tasks
    temperature=0.1,
    max_retries=5
)

# This is our main, powerful LLM for analysis
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="openai/gpt-oss-120b", # Slower but more powerful for reasoning
    temperature=0.2,
    max_retries=5
)

# <-- NEW: A fast, cheap model for the simple routing task -->
triage_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="openai/gpt-oss-20b",
    temperature=0.0, # We want this to be deterministic
    max_retries=5
)

small_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    # model="meta-llama/llama-4-scout-17b-16e-instruct", # Fast and good for structured tasks
    model="openai/gpt-oss-20b", # Fast and good for structured tasks
    temperature=0.2,
    max_retries=5
)

# They can use the main 'llm' configuration, but are defined separately for future modularity
general_medicine_llm = llm
cardiology_llm = llm
dermatology_llm = llm

# -------------------------
# Lightweight in-memory TTL cache + metrics wrapper
# -------------------------

_cache = {}
_cache_lock = threading.Lock()
_CACHE_DEFAULT_TTL = 300  # seconds

# Simple metrics collection
_metrics = {
    "calls": {},  # model_name -> count
    "tokens_in": {},
    "tokens_out": {},
}
_metrics_lock = threading.Lock()


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: average ~4 characters per token. Good enough for metrics.
    Avoids adding a tokenizer dependency in the first pass.
    """
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def _make_cache_key(model_name: str, messages, kwargs) -> str:
    payload = {"model": model_name, "messages": messages, "kwargs": kwargs}
    dumped = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def _cache_get(key: str):
    now = time.time()
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        ts, ttl, value = entry
        if now - ts > ttl:
            del _cache[key]
            return None
        return value


def _cache_set(key: str, value, ttl: int = _CACHE_DEFAULT_TTL):
    with _cache_lock:
        _cache[key] = (time.time(), ttl, value)


def _record_metrics(model_name: str, tokens_in: int, tokens_out: int):
    with _metrics_lock:
        _metrics["calls"][model_name] = _metrics["calls"].get(model_name, 0) + 1
        _metrics["tokens_in"][model_name] = _metrics["tokens_in"].get(model_name, 0) + tokens_in
        _metrics["tokens_out"][model_name] = _metrics["tokens_out"].get(model_name, 0) + tokens_out


def get_llm_metrics() -> dict:
    with _metrics_lock:
        return json.loads(json.dumps(_metrics))


def clear_llm_cache():
    with _cache_lock:
        _cache.clear()


# Monkey-patch ChatGroq instances' invoke methods so existing call sites don't need edits.
# The wrapper provides optional caching (default on) and token accounting.

def _wrap_invoke(instance, model_name: str):
    original_invoke = getattr(instance, "invoke")

    def _invoke(messages, *args, use_cache: bool = True, cache_ttl: int = _CACHE_DEFAULT_TTL, **kwargs):
        # messages is usually a list of Message objects; for cache key and token estimate, stringify simply
        try:
            msgs_serial = [m.content if hasattr(m, "content") else str(m) for m in messages]
        except Exception:
            msgs_serial = [str(m) for m in messages]

        key = _make_cache_key(model_name, msgs_serial, kwargs)
        if use_cache:
            cached = _cache_get(key)
            if cached is not None:
                return cached

        # Estimate tokens in
        tokens_in = sum(_estimate_tokens(m) for m in msgs_serial)

        # Call the original LLM invoke
        response = original_invoke(messages, *args, **kwargs)

        # Estimate tokens out conservatively: try to inspect response.content or str(response)
        try:
            # LangChain-like responses often have .content
            out_text = getattr(response, "content", None)
            if out_text is None:
                # If response is a list or has text fields, coerce to string
                out_text = str(response)
        except Exception:
            out_text = str(response)
        tokens_out = _estimate_tokens(out_text)

        _record_metrics(model_name, tokens_in, tokens_out)

        if use_cache:
            _cache_set(key, response, ttl=cache_ttl)

        return response

    # Bind the wrapper as a method
    bound = types.MethodType(_invoke, instance)
    setattr(instance, "invoke", bound)


# Apply wrappers to instances
_wrap_invoke(lab_report_llm, "lab_report_llm")
_wrap_invoke(llm, "llm")
_wrap_invoke(triage_llm, "triage_llm")
_wrap_invoke(small_llm, "small_llm")


# Convenience helpers for reducing conversation history size

def trim_history_window(history: list, max_turns: int = 8) -> list:
    """Return the last max_turns from history (list of messages/strings).
    Use this when semantics allow dropping earlier turns instead of sending full transcript.
    """
    if not history:
        return history
    return history[-max_turns:]


def summarize_and_replace_history(summarizer_llm, history: list, summary_prompt: str = None):
    """Call a small summarizer LLM to condense history into a short summary.
    This is optional and costs one LLM call, but reduces subsequent per-turn tokens.
    Returns the summary string.
    """
    if not history:
        return ""
    msgs = []
    for h in history:
        if isinstance(h, str):
            msgs.append(h)
        else:
            # Try to extract .content
            msgs.append(getattr(h, "content", str(h)))

    prompt_text = summary_prompt or "Summarize the following conversation into a concise context (3-4 sentences):\n\n" + "\n\n".join(msgs)
    # Call the summarizer (use cache=False to avoid stale summaries)
    response = summarizer_llm.invoke([type("M", (), {"content": prompt_text})], use_cache=False)
    try:
        summary = getattr(response, "content", str(response))
    except Exception:
        summary = str(response)
    return summary
