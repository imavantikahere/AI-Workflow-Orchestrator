import streamlit as st
from api_client import get_request_by_id, get_audit_logs
from api_client import (
    get_request_by_id,
    enrich_request,
    submit_request,
    approve_request,
    reject_request,
)

st.title("Request Details")

request_id = st.text_input("Enter Request ID")

if "request_data" not in st.session_state:
    st.session_state["request_data"] = None


def refresh_request():
    if request_id.strip():
        st.session_state["request_data"] = get_request_by_id(request_id.strip())


col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Load Request"):
        try:
            refresh_request()
            st.success("Request loaded.")
        except Exception as e:
            st.error(str(e))

with col2:
    if st.button("Refresh"):
        try:
            refresh_request()
            st.success("Request refreshed.")
        except Exception as e:
            st.error(str(e))

request_data = st.session_state.get("request_data")

if request_data:
    st.subheader("Request JSON")
    st.json(request_data)

    st.subheader("Approval Chain")
    approval_chain = request_data.get("approval_chain", [])
    if approval_chain:
        for idx, item in enumerate(approval_chain, start=1):
            st.write(f"{idx}. {item}")
    else:
        st.info("No approval chain available yet.")

    st.subheader("Current Status")
    st.write(f"**State:** {request_data.get('state')}")
    st.write(f"**Current Required Role:** {request_data.get('current_required_role')}")
    st.write(f"**Approval Index:** {request_data.get('approval_index')}")

    st.divider()

    st.subheader("Actions")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Run AI Enrichment"):
            try:
                result = enrich_request(request_id.strip())
                st.success("AI enrichment completed.")
                st.json(result)
                refresh_request()
            except Exception as e:
                st.error(str(e))

    with c2:
        if st.button("Submit Request"):
            try:
                result = submit_request(request_id.strip())
                st.success("Request submitted.")
                st.json(result)
                refresh_request()
            except Exception as e:
                st.error(str(e))

    with c3:
        approver_role = st.selectbox("Approver Role", ["SUPPORT_L2", "MANAGER", "DIRECTOR", "FINANCE"])

        approve_col, reject_col = st.columns(2)

        with approve_col:
            if st.button("Approve"):
                try:
                    result = approve_request(request_id.strip(), approver_role=approver_role)
                    st.success("Request approved.")
                    st.json(result)
                    refresh_request()
                except Exception as e:
                    st.error(str(e))

        with reject_col:
            reject_reason = st.text_input("Reject Reason", value="Not aligned with policy")
            if st.button("Reject"):
                try:
                    result = reject_request(
                        request_id.strip(),
                        approver_role=approver_role,
                        reason=reject_reason
                    )
                    st.success("Request rejected.")
                    st.json(result)
                    refresh_request()
                except Exception as e:
                    st.error(str(e))


    st.subheader("Audit Logs")

    try:
        audit_logs = get_audit_logs(request_id.strip())
    except Exception as e:
        st.error(f"Could not load audit logs: {e}")
        audit_logs = []

    if audit_logs:
        for log in audit_logs:
            st.markdown("---")
            st.write(f"**Action:** {log.get('action', '—')}")
            st.write(f"**Actor Name:** {log.get('actor_name', '—')}")
            st.write(f"**Actor Role:** {log.get('actor_role', '—')}")
            st.write(f"**Time:** {log.get('timestamp', '—')}")
            st.write(f"**Comments:** {log.get('comments', '—')}")
    else:
        st.info("No audit logs found for this request.")
