"""Lexio — 10-K Financial Knowledge Base frontend.

Single-page Streamlit app with custom sidebar navigation.
Pages: Chat (App), Analytics, Load Documents.
"""

import re
import uuid

import pandas as pd
import requests
import streamlit as st

from config import BACKEND_URL

# ---------------------------------------------------------------------------
# Constants & compiled patterns
# ---------------------------------------------------------------------------
_SUB_Q_RE = re.compile(
    r"^Sub question:\s*(?P<question>.+?)\s*Response:\s*(?P<response>.+)",
    re.IGNORECASE | re.DOTALL,
)

_SEPARATOR_RE = re.compile(r"^\|?[\s\-:]+\|[\s\-:|]*$")

_NUM_ROW_RE = re.compile(
    r"^\|?\s*"
    r"([\w][\w\s/&.,-]*?)"
    r"\s*\|\s*"
    r"\$?\s*(\(?)?\s*\$?\s*"
    r"([\d,]+(?:\.\d+)?)"
    r"\s*(\)?)"
    r"\s*(%?)?"
    r"\s*(billion|million|B|M|bn|mn)?"
    r"\s*\|?\s*$",
    re.MULTILINE | re.IGNORECASE,
)

_SCALE = {
    "billion": 1e9, "b": 1e9, "bn": 1e9,
    "million": 1e6, "m": 1e6, "mn": 1e6,
}


def _escape_dollars(text: str) -> str:
    """Escape bare ``$`` so Streamlit doesn't render them as LaTeX."""
    return text.replace("$", "\\$")


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lexio — 10-K Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Hide default Streamlit multi-page navigation ── */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ── Sidebar logo ── */
    .sidebar-logo {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #ffffff;
        padding: 0.25rem 0;
    }

    /* ── Hero section (chat landing) ── */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 38vh;
        padding-top: 8vh;
    }
    .hero-heading {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }

    /* ── Chat input: centered, 50-60 % width, max 720 px ── */
    [data-testid="stChatInput"] {
        max-width: 720px !important;
        width: 60% !important;
        min-width: 340px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    [data-testid="stChatInput"] > div {
        border-radius: 24px !important;
        border: 1px solid rgba(250, 250, 250, 0.12) !important;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.08) !important;
    }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }

    /* ── Sidebar buttons: left-align text ── */
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        text-align: left !important;
        justify-content: flex-start !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
_DEFAULTS: dict = {
    "page": "app",
    "messages": [],
    "backend_ok": None,
    "_ingest_settled": False,
    "usage_baseline_cost": 0.0,
    "show_hero": True,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ---------------------------------------------------------------------------
# Helpers — table extraction
# ---------------------------------------------------------------------------
def _parse_row(match: re.Match) -> tuple[str, float] | None:
    label = match.group(1).strip()
    open_paren = match.group(2)
    raw_num = match.group(3)
    close_paren = match.group(4)
    _pct = match.group(5)
    suffix = (match.group(6) or "").lower()

    try:
        value = float(raw_num.replace(",", ""))
    except ValueError:
        return None

    if open_paren == "(" and close_paren == ")":
        value = -value

    value *= _SCALE.get(suffix, 1)
    return label, value


def _try_extract_table(text: str) -> pd.DataFrame | None:
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        if _SEPARATOR_RE.match(line):
            continue
        m = _NUM_ROW_RE.match(line)
        if not m:
            continue
        parsed = _parse_row(m)
        if parsed is None:
            continue
        rows.append({"Label": parsed[0], "Value": parsed[1]})
    if len(rows) < 2:
        return None
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Helpers — rendering
# ---------------------------------------------------------------------------
def _render_sources(sources: list[dict]) -> None:
    sub_qs = [s for s in sources if s.get("source_type") == "sub_question"]
    docs = [s for s in sources if s.get("source_type") != "sub_question"]

    if sub_qs:
        with st.expander(f"Reasoning steps ({len(sub_qs)})"):
            for i, sq in enumerate(sub_qs, 1):
                m = _SUB_Q_RE.match(sq.get("text_snippet", ""))
                if m:
                    st.markdown(
                        f"**Step {i}:** {_escape_dollars(m['question'])}"
                    )
                    st.caption(_escape_dollars(m["response"]))
                else:
                    st.markdown(f"**Step {i}**")
                    st.caption(_escape_dollars(sq.get("text_snippet", "")))

    if docs:
        with st.expander(f"Sources ({len(docs)})"):
            for src in docs:
                score_pct = (
                    f"{src['score'] * 100:.1f}%"
                    if src.get("score") is not None
                    else "N/A"
                )
                st.markdown(
                    f"**{src['filename']}** · p.{src['page']} · "
                    f"Similarity score {score_pct}"
                )
                st.caption(
                    _escape_dollars(src.get("text_snippet", ""))
                    + "\n\n_Higher means semantically closer, "
                    "not guaranteed factual accuracy._"
                )


# ---------------------------------------------------------------------------
# Helpers — backend communication
# ---------------------------------------------------------------------------
def _query_backend(question: str) -> dict | None:
    payload: dict = {"question": question, "use_sub_questions": True}
    try:
        resp = requests.post(
            f"{BACKEND_URL}/query", json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        st.error("Cannot reach the backend. Is it running?")
    except requests.HTTPError as exc:
        code = exc.response.status_code
        if code == 429:
            st.error(
                "The API token budget has been exhausted — no further queries "
                "can be processed. Please increase the budget or reset usage "
                "counters and restart the system."
            )
        else:
            st.error(f"Backend error: {code} — {exc.response.text[:300]}")
    except requests.Timeout:
        st.error(
            "Request timed out. The query may be too complex — "
            "try simplifying or rephrasing the question."
        )
    return None


def _fetch_usage() -> dict | None:
    try:
        resp = requests.get(f"{BACKEND_URL}/usage", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Help dialog — "About this RAG"
# ---------------------------------------------------------------------------
@st.dialog("About this RAG", width="large")
def _help_dialog():
    st.markdown(
        "Financial analysts spend hours manually searching long SEC 10\u2011K "
        "filings to extract revenue figures, risk factors, segment breakdowns, "
        "and year\u2011over\u2011year comparisons. The information is buried in "
        "hundreds of pages of legal and financial text."
    )
    st.markdown(
        "Lexio is a Retrieval\u2011Augmented Generation (RAG) system that "
        "ingests 10\u2011K annual reports from major public companies, indexes "
        "them at page level, and answers natural\u2011language financial "
        "questions with grounded, source\u2011cited, explainable responses."
    )
    st.markdown(
        "- Semantic search with company/year filters.\n"
        "- Answers always include citations with page references.\n"
        "- Supports multi\u2011step comparative questions "
        "(e.g., revenue comparisons)."
    )
    if st.button("Got it", type="primary", use_container_width=True):
        st.rerun()


# ---------------------------------------------------------------------------
# Ingestion status banner (auto-polling fragment)
# ---------------------------------------------------------------------------
@st.fragment(run_every=3)
def _ingestion_status_banner():
    if st.session_state._ingest_settled:
        return
    try:
        r = requests.get(f"{BACKEND_URL}/ingest/status", timeout=3)
        if r.status_code == 200:
            state = r.json().get("state", "idle")
            if state == "running":
                st.info(
                    "Index warming up \u2014 documents are being loaded "
                    "in the background. You can still use the app."
                )
            else:
                st.session_state._ingest_settled = True
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">LEXIO</div>',
        unsafe_allow_html=True,
    )
    st.caption("Financial Knowledge Base")
    st.divider()

    _NAV = [
        ("app", "App"),
        ("analytics", "Analytics"),
        ("load_documents", "Documents"),
    ]
    for _pid, _lbl in _NAV:
        _active = st.session_state.page == _pid
        if st.button(
            _lbl,
            key=f"sb_{_pid}",
            use_container_width=True,
            type="primary" if _active else "secondary",
        ):
            st.session_state.page = _pid
            st.rerun()

    # Flexible spacer — pushes help/settings toward the bottom
    st.markdown(
        '<div style="min-height:calc(100vh - 560px)"></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # Help (❓) — directly above settings gear
    if st.button(
        "\u2753", key="sb_help", use_container_width=True, help="About this RAG"
    ):
        _help_dialog()

    # Settings (⚙)
    with st.popover("\u2699", use_container_width=True, help="Settings"):
        st.subheader("Settings")

        if st.button("Check backend health", key="btn_health"):
            try:
                r = requests.get(f"{BACKEND_URL}/health", timeout=5)
                st.session_state.backend_ok = r.status_code == 200
            except requests.ConnectionError:
                st.session_state.backend_ok = False

        if st.session_state.backend_ok is True:
            st.success("Backend connected")
        elif st.session_state.backend_ok is False:
            st.error("Backend unreachable")

        st.divider()

        if st.button("Reset usage baseline", key="btn_reset_usage"):
            usage = _fetch_usage()
            if usage:
                st.session_state.usage_baseline_cost = usage.get(
                    "estimated_cost_usd", 0.0
                )
                st.success("Usage metrics reset.")
            else:
                st.error("Failed to reset usage metrics.")

        if st.button("Clear chat history", key="btn_clear"):
            st.session_state.messages = []
            st.session_state.show_hero = True
            st.rerun()

        st.divider()

        if st.button("Shut Down System", type="primary", key="btn_shutdown"):
            with st.spinner("Saving data and shutting down\u2026"):
                try:
                    requests.post(f"{BACKEND_URL}/shutdown", timeout=10)
                except Exception:
                    pass
            st.session_state.messages = []
            st.success(
                "All data saved. Press Ctrl+C in the terminal to stop "
                "containers, or run `docker compose down`."
            )
            st.stop()


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
_ingestion_status_banner()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═══════════════════════════════════════════════════════════════════════════

# ── PAGE: App (Chat) ──────────────────────────────────────────────────────
if st.session_state.page == "app":

    if st.session_state.show_hero and not st.session_state.messages:
        st.markdown(
            '<div class="hero-container">'
            "<div class=\"hero-heading\">What's on your mind?</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(_escape_dollars(msg["content"]))
            if msg["role"] == "assistant":
                sources = msg.get("sources", [])
                if sources:
                    _render_sources(sources)
                df = msg.get("table")
                if df is not None:
                    st.table(df)
                    st.bar_chart(df.set_index("Label"))

    if prompt := st.chat_input("Ask me anything"):
        st.session_state.show_hero = False
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking\u2026"):
                result = _query_backend(prompt)

            if result is not None:
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                query_id = result.get("query_id") or str(uuid.uuid4())

                st.markdown(_escape_dollars(answer))

                if sources:
                    _render_sources(sources)

                df = _try_extract_table(answer)
                if df is not None:
                    st.table(df)
                    st.bar_chart(df.set_index("Label"))

                msg_entry: dict = {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "query_id": query_id,
                }
                if df is not None:
                    msg_entry["table"] = df
                st.session_state.messages.append(msg_entry)
            else:
                fallback = (
                    "Sorry, I couldn\u2019t get a response. "
                    "Please check the backend connection."
                )
                st.warning(fallback)
                st.session_state.messages.append(
                    {"role": "assistant", "content": fallback}
                )

# ── PAGE: Analytics ───────────────────────────────────────────────────────
elif st.session_state.page == "analytics":
    st.header("Analytics")

    usage = _fetch_usage()

    if usage:
        # ── Token Usage ──
        st.subheader("Token Usage")

        cost = usage.get("estimated_cost_usd", 0)
        budget = usage.get("budget_total_usd", 10)
        baseline = st.session_state.get("usage_baseline_cost", 0.0)
        adj_cost = max(cost - baseline, 0.0)
        adj_remaining = max(budget - adj_cost, 0.0)

        c1, c2 = st.columns(2)
        c1.metric("Spent (since reset)", f"${adj_cost:.4f}")
        c2.metric("Remaining", f"${adj_remaining:.2f}")
        st.progress(min(adj_cost / budget, 1.0) if budget else 0)

        with st.expander("Token details"):
            st.markdown(
                f"- **LLM prompt:** {usage.get('llm_prompt_tokens', 0):,}\n"
                f"- **LLM completion:** {usage.get('llm_completion_tokens', 0):,}\n"
                f"- **Embedding:** {usage.get('embedding_tokens', 0):,}"
            )

        st.divider()

        # ── Token Efficiency ──
        st.subheader("Token Efficiency")

        prompt_tok = usage.get("llm_prompt_tokens", 0)
        completion_tok = usage.get("llm_completion_tokens", 0)
        embed_tok = usage.get("embedding_tokens", 0)
        total_tok = prompt_tok + completion_tok + embed_tok

        e1, e2, e3 = st.columns(3)
        e1.metric("Total Tokens", f"{total_tok:,}")
        e2.metric(
            "Completion / Prompt",
            (
                f"{completion_tok / prompt_tok:.2f}"
                if prompt_tok > 0
                else "N/A"
            ),
        )
        e3.metric(
            "Cost per 1K Tokens",
            (
                f"${(cost / total_tok * 1000):.4f}"
                if total_tok > 0
                else "N/A"
            ),
        )

        if total_tok > 0:
            st.markdown("**Token Distribution**")
            dist_df = pd.DataFrame(
                {
                    "Category": ["LLM Prompt", "LLM Completion", "Embedding"],
                    "Tokens": [prompt_tok, completion_tok, embed_tok],
                }
            )
            st.bar_chart(dist_df.set_index("Category"))
    else:
        st.warning("Usage data unavailable. Is the backend running?")

# ── PAGE: Load Documents ──────────────────────────────────────────────────
elif st.session_state.page == "load_documents":
    st.header("Load Documents")
    st.caption("Ingest 10-K annual reports into the knowledge base")

    force = st.checkbox(
        "Force reload",
        value=False,
        key="ld_force",
        help="Rebuild the index even if documents were already loaded.",
    )

    if st.button("Load Documents", type="primary", key="btn_load"):
        with st.spinner("Loading documents\u2026"):
            try:
                r = requests.post(
                    f"{BACKEND_URL}/ingest",
                    json={"force": force},
                    timeout=600,
                )
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") == "skipped":
                        st.info(
                            f"Documents already loaded "
                            f"({data.get('existing_chunks', 0)} chunks). "
                            f"Enable **Force reload** to re-index."
                        )
                    else:
                        st.success(
                            f"Loaded {data.get('documents_processed', 0)} "
                            f"documents \u2014 "
                            f"{data.get('chunks_created', 0)} chunks created."
                        )
                else:
                    st.error(
                        f"Loading failed: {r.status_code} \u2014 "
                        f"{r.text[:200]}"
                    )
            except requests.ConnectionError:
                st.error("Cannot reach the backend. Is it running?")
            except requests.Timeout:
                st.error("Loading timed out.")
            except Exception as exc:
                st.error(f"Loading failed: {exc}")

    st.divider()
    st.subheader("Available Documents")
    st.markdown(
        "| Company | FY 2023 | FY 2024 | FY 2025 |\n"
        "|---------|---------|---------|---------|\n"
        "| NVIDIA | `10k_2023.pdf` | `10k_2024.pdf` | `10k_2025.pdf` |\n"
        "| Alphabet (Google) | `10k_2023.pdf` | `10k_2024.pdf` | `10k_2025.pdf` |\n"
        "| Apple | `10k_2023.pdf` | `10k_2024.pdf` | `10k_2025.pdf` |\n"
        "| Microsoft | `10k_2023.pdf` | `10k_2024.pdf` | `10k_2025.pdf` |\n"
        "| Tesla | `10k_2023.pdf` | `10k_2024.pdf` | `10k_2025.pdf` |"
    )
