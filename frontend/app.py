import os
import re
import uuid

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
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

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "backend_ok" not in st.session_state:
    st.session_state.backend_ok = None

# ---------------------------------------------------------------------------
# Sidebar — filters & settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("PageIndex RAG")
    st.caption("10-K Financial Knowledge Base")
    st.divider()

    selected_companies = st.multiselect(
        "Companies",
        options=COMPANIES,
        default=[],
        help="Leave empty to search all companies.",
    )
    selected_years = st.multiselect(
        "Years",
        options=YEARS,
        default=[],
        help="Leave empty to search all years.",
    )
    use_sub_questions = st.toggle(
        "Sub-question decomposition",
        value=False,
        help="Break complex / comparative queries into sub-questions for multi-step reasoning.",
    )

    st.divider()

    if st.button("Check backend health"):
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
    ingest_col1, ingest_col2 = st.columns(2)
    with ingest_col1:
        ingest_btn = st.button("Ingest Documents")
    with ingest_col2:
        force_reingest = st.checkbox("Force re-ingest", value=False)

    if ingest_btn:
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

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

    # ---- API token usage (placeholder — updated after queries) ------------
    st.divider()
    _usage_placeholder = st.empty()

    # ---- Shutdown button --------------------------------------------------
    st.divider()
    if st.button("Shut Down System", type="primary"):
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


def _render_usage(container) -> None:
    """Fetch /usage and render metrics inside the given container."""
    with container.container():
        st.subheader("API Usage")
        try:
            resp = requests.get(f"{BACKEND_URL}/usage", timeout=5)
            if resp.status_code == 200:
                u = resp.json()
                cost = u.get("estimated_cost_usd", 0)
                remaining = u.get("budget_remaining_usd", 0)
                budget = u.get("budget_total_usd", 10)

                col_a, col_b = st.columns(2)
                col_a.metric("Spent", f"${cost:.4f}")
                col_b.metric("Remaining", f"${remaining:.2f}")
                st.progress(min(cost / budget, 1.0) if budget else 0)

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


_render_usage(_usage_placeholder)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _query_backend(question: str) -> dict | None:
    """POST to /query and return the JSON response, or None on failure."""
    payload: dict = {"question": question}
    if selected_companies:
        payload["companies"] = [c.lower() for c in selected_companies]
    if selected_years:
        payload["years"] = selected_years
    if use_sub_questions:
        payload["use_sub_questions"] = True

    try:
        resp = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        st.error("Cannot reach the backend. Is it running?")
    except requests.HTTPError as exc:
        st.error(f"Backend error: {exc.response.status_code} — {exc.response.text[:300]}")
    except requests.Timeout:
        st.error("Request timed out. The query may be too complex — try narrowing filters.")
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


_NUM_ROW_RE = re.compile(
    r"^\|?\s*([A-Za-z][\w\s/&.-]*?)\s*\|"
    r"\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:billion|million|B|M|bn|mn)?\s*\|",
    re.MULTILINE,
)


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
                    f"**{src['filename']}** · p.{src['page']} · relevance {score_pct}"
                )
                st.caption(_escape_dollars(src.get("text_snippet", "")))


def _try_extract_table(text: str) -> pd.DataFrame | None:
    """Best-effort extraction of a simple label|value markdown table."""
    matches = _NUM_ROW_RE.findall(text)
    if len(matches) < 2:
        return None
    rows = []
    for label, raw_value in matches:
        try:
            value = float(raw_value.replace(",", ""))
            rows.append({"Label": label.strip(), "Value": value})
        except ValueError:
            continue
    if len(rows) < 2:
        return None
    return pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
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

            qid = msg.get("query_id", "")
            fb_key = f"fb_{qid}"
            if fb_key not in st.session_state:
                st.session_state[fb_key] = None

            col1, col2, _ = st.columns([1, 1, 10])
            with col1:
                if st.button("👍", key=f"up_{qid}"):
                    _send_feedback(qid, "up")
                    st.session_state[fb_key] = "up"
            with col2:
                if st.button("👎", key=f"down_{qid}"):
                    _send_feedback(qid, "down")
                    st.session_state[fb_key] = "down"

            if st.session_state.get(fb_key):
                st.caption(f"Feedback recorded: {st.session_state[fb_key]}")

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask about 10-K filings…"):
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

            fb_key = f"fb_{query_id}"
            st.session_state[fb_key] = None
            col1, col2, _ = st.columns([1, 1, 10])
            with col1:
                if st.button("👍", key=f"up_{query_id}"):
                    _send_feedback(query_id, "up")
                    st.session_state[fb_key] = "up"
            with col2:
                if st.button("👎", key=f"down_{query_id}"):
                    _send_feedback(query_id, "down")
                    st.session_state[fb_key] = "down"

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
