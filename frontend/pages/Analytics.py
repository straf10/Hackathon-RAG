"""
Analytics dashboard — displays feedback stats from the backend.
FR-UI-07: Total Queries, Positive %, Negative %.
"""

import requests
import streamlit as st

from config import BACKEND_URL

st.set_page_config(page_title="Analytics — PageIndex RAG", page_icon="📈", layout="wide")
st.title("Feedback Analytics")
st.caption("Aggregated query feedback statistics")

try:
    r = requests.get(f"{BACKEND_URL}/feedback/stats", timeout=10)
    r.raise_for_status()
    stats = r.json()
except requests.ConnectionError:
    st.error("Cannot reach the backend. Is it running?")
    st.stop()
except requests.HTTPError as exc:
    st.error(f"Backend error: {exc.response.status_code}")
    st.stop()

total = stats.get("total_queries", 0)
pos_pct = stats.get("positive_percentage", 0.0)
neg_pct = stats.get("negative_percentage", 0.0)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Queries", total)
with col2:
    st.metric("Positive %", f"{pos_pct:.1f}%")
with col3:
    st.metric("Negative %", f"{neg_pct:.1f}%")

if total > 0:
    st.divider()
    st.subheader("Distribution")
    st.progress(pos_pct / 100.0, text=f"Positive: {pos_pct:.1f}%")
    st.progress(neg_pct / 100.0, text=f"Negative: {neg_pct:.1f}%")
else:
    st.info("No feedback recorded yet. Submit queries and rate responses to see analytics.")

st.divider()
st.subheader("Recent Feedback")
try:
    r_recent = requests.get(f"{BACKEND_URL}/feedback/recent", params={"limit": 20}, timeout=10)
    r_recent.raise_for_status()
    recent = r_recent.json()
except requests.ConnectionError:
    st.warning("Cannot reach the backend. Recent feedback unavailable.")
    recent = []
except requests.HTTPError as exc:
    st.warning(f"Backend error {exc.response.status_code}. Recent feedback unavailable.")
    recent = []

if recent:
    table_data = [["Timestamp", "Query ID", "Rating", "Comment"]] + [
        [
            e.get("created_at", ""),
            e.get("query_id", ""),
            e.get("rating", ""),
            (e.get("comment") or ""),
        ]
        for e in recent
    ]
    st.table(table_data)
else:
    st.info("No recent feedback entries.")
