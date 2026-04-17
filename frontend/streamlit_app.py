import streamlit as st
from api_client import BASE_URL

st.set_page_config(
    page_title="AI Workflow Frontend",
    page_icon="🧠",
    layout="wide"
)

st.title("AI Workflow Frontend")
st.caption("Streamlit UI for your FastAPI-based workflow engine")

st.info(f"Connected API base URL: {BASE_URL}")

st.markdown(
    """
### What you can do here
- Create workflow requests
- View all requests
- Open a request by ID
- Trigger AI enrichment
- Submit into approval flow
- Approve or reject requests
"""
)

st.success("Use the left sidebar to navigate between pages.")