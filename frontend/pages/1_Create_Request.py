import streamlit as st
from api_client import create_request, submit_request

st.title("Create Request")


REQUEST_TYPES = [
    "PROCUREMENT",
    "LEAVE",
    "SUPPORT",
    "FINANCE",
    "HR",
    "UNKNOWN"
] 

with st.form("create_request_form"):
    title = st.text_input("Title")
    description = st.text_area("Description")
    created_by = st.text_input("Created By")
    request_type = st.selectbox("Request Type", REQUEST_TYPES)

    amount = st.number_input("Amount", min_value=0.0, step=500.0, value=0.0)
    leave_days = st.number_input("Leave Days", min_value=0, step=1, value=0)
    severity = st.selectbox("Severity", ["", "LOW", "MEDIUM", "HIGH", "CRITICAL"])

    auto_submit = st.checkbox("Automatically submit after creation", value=True)

    submitted = st.form_submit_button("Create Request")

if submitted:
    try:
        payload = {
            "title": title,
            "description": description,
            "created_by": created_by,
            "request_type": request_type,
        }

        # Add optional fields only when relevant
        if request_type == "PROCUREMENT":
            payload["amount"] = amount
        elif request_type == "LEAVE":
            payload["leave_days"] = leave_days
        elif request_type == "SUPPORT" and severity:
            payload["severity"] = severity
        elif request_type == "FINANCE":
            payload["amount"] = amount
        #elif request_type == "HR":
            #pass  # No additional fields needed for HR requests


        # Step 1: create request
        create_result = create_request(payload)

        if not isinstance(create_result, dict) or "id" not in create_result:
            st.error("Request was created, but no request ID was returned.")
            st.json(create_result)
            st.stop()

        request_id = create_result["id"]

        st.success(f"Request created successfully: {request_id}")
        st.json(create_result)

        # Step 2: submit request so approval chain is created
        if auto_submit:
            submit_result = submit_request(request_id)

            st.success("Request submitted successfully. Approval chain should now be created.")
            st.subheader("Submitted Request")
            st.json(submit_result)

            approval_chain = submit_result.get("approval_chain", [])
            if approval_chain:
                st.subheader("Approval Chain")
                for idx, role in enumerate(approval_chain, start=1):
                    st.write(f"{idx}. {role}")
            else:
                st.warning("Request submitted, but no approval chain was returned.")

    except Exception as e:
        st.error(str(e))
