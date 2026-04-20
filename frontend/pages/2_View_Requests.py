import streamlit as st
import pandas as pd
from api_client import get_all_requests

st.title("All Requests")

if st.button("Refresh Requests", type="secondary"):
    st.session_state["refresh_requests"] = True

try:
    data = get_all_requests()

    if isinstance(data, list) and data:
        df = pd.DataFrame(data)

        st.subheader("Request Table")

        filter_state = st.selectbox(
            "Filter by State",
            options=["ALL"] + sorted(df["state"].dropna().unique().tolist()) if "state" in df.columns else ["ALL"]
        )

        filter_type = st.selectbox(
            "Filter by Request Type",
            options=["ALL"] + sorted(df["request_type"].dropna().unique().tolist()) if "request_type" in df.columns else ["ALL"]
        )

        filter_role = st.selectbox(
            "Filter by Current Required Role",
            options=["ALL"] + sorted(df["current_required_role"].dropna().unique().tolist()) if "current_required_role" in df.columns else ["ALL"]
        )

        filtered_df = df.copy()

        if filter_state != "ALL" and "state" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["state"] == filter_state]

        if filter_type != "ALL" and "request_type" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["request_type"] == filter_type]

        if filter_role != "ALL" and "current_required_role" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["current_required_role"] == filter_role]

        st.dataframe(filtered_df, use_container_width=True)

    elif isinstance(data, list) and not data:
        st.warning("No requests found.")
    else:
        st.json(data)

except Exception as e:
    st.error(str(e))
