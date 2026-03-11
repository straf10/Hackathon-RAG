import re
import uuid

import pandas as pd
import requests
import streamlit as st

from config import BACKEND_URL
COMPANIES = ["NVIDIA", "Google", "Apple"]
YEARS = [2024, 2025]

_SUB_Q_RE = re.compile(
    r"^Sub question:\s*(?P<question>.+?)\s*Response:\s*(?P<response>.+)",
    re.IGNORECASE | re.DOTALL,
)


def _escape_dollars(text: str) -> str:
    """Escape bare ``$`` so Streamlit doesn't render them as LaTeX."""
    return text.replace("$", "\\$")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PageIndex RAG — 10-K Analysis", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .lexio-main-container {
        max-width: 900px;
        margin: 0 auto;
        padding-top: 3rem;
    }
    .lexio-hero {
        text-align: center;
        margin-bottom: 3rem;
    }
    .lexio-hero-title {
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: 0.15em;
    }
    .lexio-hero-subtitle {
        font-size: 1.1rem;
        color: rgba(250, 250, 250, 0.8);
        margin-top: 0.5rem;
    }
    .stChatMessage {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    .stChatInput {
        max-width: 900px;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "backend_ok" not in st.session_state:
    st.session_state.backend_ok = None
if "_ingest_settled" not in st.session_state:
    st.session_state._ingest_settled = False
if "usage_baseline_cost" not in st.session_state:
    st.session_state.usage_baseline_cost = 0.0
if "show_hero" not in st.session_state:
    st.session_state.show_hero = True


def _render_usage(container) -> None:
    """Fetch /usage and render metrics inside the given container."""
    with container.container():
        st.subheader("API Usage")
        try:
            resp = requests.get(f"{BACKEND_URL}/usage", timeout=5)
            if resp.status_code == 200:
                u = resp.json()
                cost = u.get("estimated_cost_usd", 0)
                budget = u.get("budget_total_usd", 10)
                baseline = st.session_state.get("usage_baseline_cost", 0.0)
                adj_cost = max(cost - baseline, 0.0)
                adj_remaining = max(budget - adj_cost, 0.0)

                col_a, col_b = st.columns(2)
                col_a.metric("Spent (since reset)", f"${adj_cost:.4f}")
                col_b.metric("Remaining", f"${adj_remaining:.2f}")
                st.progress(min(adj_cost / budget, 1.0) if budget else 0)

                with st.expander("Token details"):
                    st.markdown(
                        f"- **LLM prompt:** {u.get('llm_prompt_tokens', 0):,}\n"
                        f"- **LLM completion:** {u.get('llm_completion_tokens', 0):,}\n"
                        f"- **Embedding:** {u.get('embedding_tokens', 0):,}"
                    )
            else:
                st.caption("Usage data unavailable")
        except Exception:
            st.caption("Usage data unavailable")


# ---------------------------------------------------------------------------
# Sidebar — minimal, with usage metrics
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("**Lexio**")
    st.caption("10-K Financial Knowledge Base")
    st.divider()
    _usage_placeholder = st.empty()
    _render_usage(_usage_placeholder)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _query_backend(question: str) -> dict | None:
    """POST to /query and return the JSON response, or None on failure."""
    payload: dict = {"question": question, "use_sub_questions": True}

    try:
        resp = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=120)
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
        st.error("Request timed out. The query may be too complex — try simplifying or rephrasing the question.")
    return None


def _send_feedback(query_id: str, rating: str) -> None:
    """POST to /feedback. Failures are silently logged."""
    try:
        requests.post(
            f"{BACKEND_URL}/feedback",
            json={"query_id": query_id, "rating": rating},
            timeout=10,
        )
    except Exception:
        pass


def _render_feedback_buttons(query_id: str) -> None:
    """Render thumbs-up / thumbs-down feedback buttons for a response."""
    fb_key = f"fb_{query_id}"
    if fb_key not in st.session_state:
        st.session_state[fb_key] = None

    col1, col2, _ = st.columns([1, 1, 10])
    with col1:
        if st.button("\U0001f44d", key=f"up_{query_id}"):
            _send_feedback(query_id, "up")
            st.session_state[fb_key] = "up"
    with col2:
        if st.button("\U0001f44e", key=f"down_{query_id}"):
            _send_feedback(query_id, "down")
            st.session_state[fb_key] = "down"

    if st.session_state.get(fb_key):
        st.caption(f"Feedback recorded: {st.session_state[fb_key]}")


_SEPARATOR_RE = re.compile(r"^\|?[\s\-:]+\|[\s\-:|]*$")

_NUM_ROW_RE = re.compile(
    r"^\|?\s*"
    r"([\w][\w\s/&.,-]*?)"            # label: may start with digit or letter
    r"\s*\|\s*"
    r"\$?\s*(\(?)?\s*\$?\s*"           # optional $, optional opening paren
    r"([\d,]+(?:\.\d+)?)"              # number
    r"\s*(\)?)"                         # optional closing paren
    r"\s*(%?)?"                         # optional percent
    r"\s*(billion|million|B|M|bn|mn)?" # optional scale suffix
    r"\s*\|?\s*$",                      # trailing pipe optional
    re.MULTILINE | re.IGNORECASE,
)

_SCALE = {
    "billion": 1e9, "b": 1e9, "bn": 1e9,
    "million": 1e6, "m": 1e6, "mn": 1e6,
}


def _parse_row(match: re.Match) -> tuple[str, float] | None:
    """Convert a regex match into (label, numeric_value), applying sign,
    scale, and percentage rules.  Returns None on parse failure."""
    label = match.group(1).strip()
    open_paren = match.group(2)
    raw_num = match.group(3)
    close_paren = match.group(4)
    pct = match.group(5)
    suffix = (match.group(6) or "").lower()

    try:
        value = float(raw_num.replace(",", ""))
    except ValueError:
        return None

    if open_paren == "(" and close_paren == ")":
        value = -value

    value *= _SCALE.get(suffix, 1)

    return label, value


def _render_sources(sources: list[dict]) -> None:
    """Render source citations, separating sub-question reasoning steps
    from actual document sources."""
    sub_qs = [s for s in sources if s.get("source_type") == "sub_question"]
    docs = [s for s in sources if s.get("source_type") != "sub_question"]

    if sub_qs:
        with st.expander(f"Reasoning steps ({len(sub_qs)})"):
            for i, sq in enumerate(sub_qs, 1):
                m = _SUB_Q_RE.match(sq.get("text_snippet", ""))
                if m:
                    st.markdown(f"**Step {i}:** {_escape_dollars(m['question'])}")
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
                    f"**{src['filename']}** · p.{src['page']} · Similarity score {score_pct}"
                )
                st.caption(
                    _escape_dollars(src.get("text_snippet", ""))
                    + "\n\n_Higher means semantically closer, not guaranteed factual accuracy._"
                )


def _try_extract_table(text: str) -> pd.DataFrame | None:
    """Best-effort extraction of a simple label|value markdown table."""
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
# Auto-ingest status banner (polls backend until ingestion settles)
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
                    "Index warming up \u2014 documents are being ingested "
                    "in the background. You can still use the app."
                )
            else:
                st.session_state._ingest_settled = True
    except Exception:
        pass

_ingestion_status_banner()

# ---------------------------------------------------------------------------
# Main header and settings gear
# ---------------------------------------------------------------------------
col_title, col_gear = st.columns([12, 1])
with col_title:
    st.write("")  # spacer

with col_gear:
    with st.popover("⚙ Settings", use_container_width=True):
        st.caption("Advanced controls")

        if st.button("Check backend health", key="btn_check_health"):
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
        force_reingest = st.checkbox(
            "Force re-ingest",
            value=False,
            key="chk_force_reingest",
            help="Rebuild the index even if documents were already ingested.",
        )
        if st.button("Run ingestion", key="btn_run_ingest"):
            with st.spinner("Ingesting documents…"):
                try:
                    r = requests.post(
                        f"{BACKEND_URL}/ingest",
                        json={"force": force_reingest},
                        timeout=600,
                    )
                    if r.status_code == 200:
                        data = r.json()
                        if data.get("status") == "skipped":
                            st.info(
                                f"Documents already ingested "
                                f"({data.get('existing_chunks', 0)} chunks in database). "
                                f"Enable **Force re-ingest** to reload."
                            )
                        else:
                            st.success(
                                f"Ingested {data.get('documents_processed', 0)} docs, "
                                f"{data.get('chunks_created', 0)} chunks created."
                            )
                    else:
                        st.error(f"Ingestion failed: {r.status_code} — {r.text[:200]}")
                except requests.ConnectionError:
                    st.error("Cannot reach the backend. Is it running?")
                except requests.Timeout:
                    st.error("Ingestion timed out.")
                except Exception as exc:
                    st.error(f"Ingestion failed: {exc}")

        st.divider()
        if st.button("Reset usage baseline", key="btn_reset_usage"):
            try:
                resp = requests.get(f"{BACKEND_URL}/usage", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.usage_baseline_cost = data.get("estimated_cost_usd", 0.0)
                    st.success("Usage metrics reset. Totals are now counted from this point.")
                else:
                    st.error("Unable to retrieve usage data to reset.")
            except Exception:
                st.error("Failed to reset usage metrics.")

        st.divider()
        if st.button("Clear chat history", key="btn_clear_chat"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Shut Down System", type="primary", key="btn_shutdown"):
            with st.spinner("Saving data and shutting down…"):
                try:
                    requests.post(f"{BACKEND_URL}/shutdown", timeout=10)
                except Exception:
                    pass
            st.session_state.messages = []
            st.success(
                "All data has been saved. "
                "Press **Ctrl+C** in the terminal to stop the containers, "
                "or run `docker compose down` to shut down completely."
            )
            st.stop()

# ---------------------------------------------------------------------------
# Centered main chat region with optional Lexio hero
# ---------------------------------------------------------------------------
main_container = st.container()
with main_container:
    if st.session_state.show_hero and not st.session_state.messages:
        st.markdown(
            """
            <div class="lexio-main-container">
              <div class="lexio-hero">
                <div class="lexio-hero-title">LEXIO</div>
              </div>
            </div>
            """,
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

                _render_feedback_buttons(msg.get("query_id", ""))

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask Lexio …"):
    st.session_state.show_hero = False
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
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

            _render_feedback_buttons(query_id)

            msg_entry = {
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "query_id": query_id,
            }
            if df is not None:
                msg_entry["table"] = df
            st.session_state.messages.append(msg_entry)

            _render_usage(_usage_placeholder)
        else:
            fallback = "Sorry, I couldn't get a response. Please check the backend connection."
            st.warning(fallback)
            st.session_state.messages.append({"role": "assistant", "content": fallback})
