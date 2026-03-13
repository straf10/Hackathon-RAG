"""
Global token usage tracker using LlamaIndex's TokenCountingHandler.

Counts all LLM (prompt + completion) and embedding tokens flowing through
LlamaIndex, estimates cost based on model pricing, and exposes a snapshot
via ``get_usage()``.

Usage is persisted to a JSON file on the app_data volume so totals
survive container restarts.

Call ``install()`` once at application startup — before any LlamaIndex
models are created — to wire the callback into ``Settings.callback_manager``.
"""

import json
import logging
import threading
from pathlib import Path

import tiktoken
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

from ..config import settings as app_settings

logger = logging.getLogger(__name__)

# ---- pricing (USD per 1 M tokens) ----------------------------------------
_LLM_INPUT_COST = 2.5      # gpt-4.1 input
_LLM_OUTPUT_COST = 8.00       # gpt-4.1 output
_EMBED_COST = 0.02            # text-embedding-3-small
_BUDGET_USD = 10.00

# ---- persistence ----------------------------------------------------------
_USAGE_FILE = Path(app_settings.APP_DATA_DIR) / "token_usage.json"

_historical: dict[str, int] = {"prompt": 0, "completion": 0, "embedding": 0}
_persist_lock = threading.Lock()


def _load_historical() -> None:
    """Load persisted cumulative totals from disk."""
    global _historical
    try:
        if _USAGE_FILE.exists():
            data = json.loads(_USAGE_FILE.read_text())
            _historical = {
                "prompt": int(data.get("prompt", 0)),
                "completion": int(data.get("completion", 0)),
                "embedding": int(data.get("embedding", 0)),
            }
            logger.info("Loaded historical token usage: %s", _historical)
    except Exception:
        logger.warning("Could not load %s — starting from zero", _USAGE_FILE, exc_info=True)


def _save_historical() -> None:
    """Write cumulative totals to disk."""
    try:
        _USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _USAGE_FILE.write_text(json.dumps(_historical, indent=2))
    except Exception:
        logger.warning("Could not save usage to %s", _USAGE_FILE, exc_info=True)


# ---- tokenizer -----------------------------------------------------------
try:
    _tokenizer = tiktoken.encoding_for_model("gpt-4.1").encode
except KeyError:
    _tokenizer = tiktoken.get_encoding("cl100k_base").encode

# ---- singleton handler & callback manager ---------------------------------
token_counter = TokenCountingHandler(tokenizer=_tokenizer, verbose=False)
callback_manager = CallbackManager([token_counter])


# ---- public API -----------------------------------------------------------

def install() -> None:
    """Inject the callback manager into LlamaIndex's global Settings and
    load persisted usage from disk."""
    _load_historical()
    Settings.callback_manager = callback_manager
    logger.info("Token-tracking callback installed")


def persist() -> None:
    """Flush in-memory session counters into the historical totals and save
    to disk.  Call this **after** an LLM/embedding operation has completed
    (not while one is in flight) to avoid losing tokens mid-operation."""
    with _persist_lock:
        delta_p = token_counter.prompt_llm_token_count
        delta_c = token_counter.completion_llm_token_count
        delta_e = token_counter.total_embedding_token_count

        if not (delta_p or delta_c or delta_e):
            return

        _historical["prompt"] += delta_p
        _historical["completion"] += delta_c
        _historical["embedding"] += delta_e
        token_counter.reset_counts()
        _save_historical()
        logger.info(
            "Persisted token usage (+%d prompt, +%d completion, +%d embed)",
            delta_p, delta_c, delta_e,
        )


def get_usage() -> dict:
    """Return a snapshot of cumulative token usage and estimated cost.

    Includes both persisted historical totals and any tokens accumulated
    in the current session that haven't been flushed yet."""
    prompt = _historical["prompt"] + token_counter.prompt_llm_token_count
    completion = _historical["completion"] + token_counter.completion_llm_token_count
    embedding = _historical["embedding"] + token_counter.total_embedding_token_count

    llm_input_cost = (prompt / 1_000_000) * _LLM_INPUT_COST
    llm_output_cost = (completion / 1_000_000) * _LLM_OUTPUT_COST
    embed_cost = (embedding / 1_000_000) * _EMBED_COST
    total_cost = llm_input_cost + llm_output_cost + embed_cost

    return {
        "llm_prompt_tokens": prompt,
        "llm_completion_tokens": completion,
        "llm_total_tokens": prompt + completion,
        "embedding_tokens": embedding,
        "estimated_cost_usd": round(total_cost, 6),
        "budget_total_usd": _BUDGET_USD,
        "budget_remaining_usd": round(max(_BUDGET_USD - total_cost, 0), 6),
    }


def reset() -> None:
    """Reset all counters and persisted data (useful for testing)."""
    global _historical
    _historical = {"prompt": 0, "completion": 0, "embedding": 0}
    token_counter.reset_counts()
    _save_historical()
    logger.info("Token counters and persisted usage reset")
