import streamlit as st
from api_client import create_request

st.title("Create Request")

REQUEST_TYPES = [
    "PROCUREMENT",
    "LEAVE",
    "INCIDENT",
    "GENERAL"
]

with st.form("create_request_form"):
    title = st.text_input("Title")
    description = st.text_area("Description")
    created_by = st.text_input("Created By", value="Avantika")
    request_type = st.selectbox("Request Type", REQUEST_TYPES)

    amount = st.number_input("Amount", min_value=0.0, step=500.0, value=0.0)
    leave_days = st.number_input("Leave Days", min_value=0, step=1, value=0)
    severity = st.selectbox("Severity", ["", "LOW", "MEDIUM", "HIGH", "CRITICAL"])

    submitted = st.form_submit_button("Create Request")

if submitted:
    try:
        payload = {
            "title": title,
            "description": description,
            "created_by": created_by,
            "request_type": request_type,
        }

        # Only send relevant optional fields
        if request_type == "PROCUREMENT":
            payload["amount"] = amount
        elif request_type == "LEAVE":
            payload["leave_days"] = leave_days
        elif request_type == "INCIDENT" and severity:
            payload["severity"] = severity

        result = create_request(payload)
        st.success("Request created successfully.")
        st.json(result)

        if isinstance(result, dict) and "id" in result:
            st.code(result["id"], language="text")

    except Exception as e:
        st.error(str(e))