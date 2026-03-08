import os
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Financial RAG", page_icon="📊", layout="wide")
st.title("Financial RAG - Chat")

try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        st.success("Backend is connected!")
    else:
        st.warning("Backend returned unexpected status")
except requests.ConnectionError:
    st.error("Cannot connect to backend. Is it running?")

st.chat_input("Ask a question about financial reports...")
