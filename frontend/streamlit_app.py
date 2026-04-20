import streamlit as st
from api_client import BASE_URL

st.set_page_config(
    page_title="AI Workflow Frontend",
    page_icon="🧠",
    layout="wide"
)

st.title("AI Workflow Orchestrator - Streamlit Frontend")
st.caption("Streamlit UI for the FastAPI-based workflow engine")

st.info(f"Connected API base URL: {BASE_URL}")

st.markdown(
    """
### Available pages
- Create Request
- View Requests
- Request Details
- Approval Dashboard
"""
)

st.success("Use the left sidebar to navigate between pages.")
