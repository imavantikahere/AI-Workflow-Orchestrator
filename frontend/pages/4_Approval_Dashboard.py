import pandas as pd
import streamlit as st

from api_client import get_all_requests, approve_request, reject_request

st.set_page_config(page_title="Approval Dashboard", page_icon="✅", layout="wide")
st.title("Approval Dashboard")

st.caption("View pending approvals, current approver role, approval chain, and take actions.")

# -----------------------------
# Helpers
# -----------------------------
def safe_list(value):
    return value if isinstance(value, list) else []

def current_approver_display(row):
    return row.get("current_required_role") or "—"

def approval_chain_display(row):
    chain = safe_list(row.get("approval_chain"))
    return " → ".join(chain) if chain else "—"

def approval_progress_display(row):
    chain = safe_list(row.get("approval_chain"))
    idx = row.get("approval_index", 0)

    if not chain:
        return "0 / 0"

    try:
        idx = int(idx)
    except Exception:
        idx = 0

    return f"{min(idx, len(chain))} / {len(chain)}"

def state_badge(state: str) -> str:
    if not state:
        return "UNKNOWN"
    return state.upper()

# -----------------------------
# Load data
# -----------------------------


if st.button("Refresh Dashboard"):
    st.rerun()

try:
    requests_data = get_all_requests()
except Exception as e:
    st.error(f"Could not load requests: {e}")
    st.stop()

if not isinstance(requests_data, list) or len(requests_data) == 0:
    st.warning("No workflow requests found.")
    st.stop()

df = pd.DataFrame(requests_data)

# Ensure expected columns exist
expected_cols = [
    "id",
    "title",
    "created_by",
    "request_type",
    "state",
    "amount",
    "leave_days",
    "severity",
    "current_required_role",
    "approval_chain",
    "approval_index",
    "created_at",
    "updated_at",
]
for col in expected_cols:
    if col not in df.columns:
        df[col] = None

# Derived fields
df["approval_chain_display"] = df.apply(approval_chain_display, axis=1)
df["approval_progress"] = df.apply(approval_progress_display, axis=1)
df["current_approver"] = df.apply(current_approver_display, axis=1)

# -----------------------------
# Top metrics
# -----------------------------
total_requests = len(df)
pending_requests = len(df[df["state"].astype(str).str.upper().isin(["PENDING", "SUBMITTED", "IN_REVIEW"])])
approved_requests = len(df[df["state"].astype(str).str.upper() == "APPROVED"])
rejected_requests = len(df[df["state"].astype(str).str.upper() == "REJECTED"])
draft_requests = len(df[df["state"].astype(str).str.upper() == "DRAFT"])

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total", total_requests)
m2.metric("Pending", pending_requests)
m3.metric("Approved", approved_requests)
m4.metric("Rejected", rejected_requests)
m5.metric("Draft", draft_requests)

st.divider()

# -----------------------------
# Filters
# -----------------------------
f1, f2, f3 = st.columns(3)

with f1:
    states = ["ALL"] + sorted([str(x) for x in df["state"].dropna().unique().tolist()])
    selected_state = st.selectbox("Filter by State", states)

with f2:
    request_types = ["ALL"] + sorted([str(x) for x in df["request_type"].dropna().unique().tolist()])
    selected_type = st.selectbox("Filter by Request Type", request_types)

with f3:
    roles = ["ALL"] + sorted([str(x) for x in df["current_required_role"].dropna().unique().tolist()])
    selected_role = st.selectbox("Filter by Current Required Role", roles)

filtered_df = df.copy()

if selected_state != "ALL":
    filtered_df = filtered_df[filtered_df["state"].astype(str) == selected_state]

if selected_type != "ALL":
    filtered_df = filtered_df[filtered_df["request_type"].astype(str) == selected_type]

if selected_role != "ALL":
    filtered_df = filtered_df[filtered_df["current_required_role"].astype(str) == selected_role]

st.subheader("Approval Queue")

display_columns = [
    "id",
    "title",
    "created_by",
    "request_type",
    "state",
    "current_approver",
    "approval_progress",
    "approval_chain_display",
    "amount",
    "leave_days",
    "severity",
    "created_at",
]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True
)

st.divider()

# -----------------------------
# Action panel
# -----------------------------
st.subheader("Take Approval Action")

request_options = filtered_df["id"].dropna().astype(str).tolist()

if not request_options:
    st.info("No requests available for the selected filters.")
    st.stop()

selected_request_id = st.selectbox("Select Request ID", request_options)

selected_row = filtered_df[filtered_df["id"].astype(str) == selected_request_id].iloc[0]

c1, c2 = st.columns([1, 1])

with c1:
    st.markdown("### Request Summary")
    st.write(f"**Title:** {selected_row.get('title', '—')}")
    st.write(f"**Created By:** {selected_row.get('created_by', '—')}")
    st.write(f"**Request Type:** {selected_row.get('request_type', '—')}")
    st.write(f"**State:** {state_badge(selected_row.get('state'))}")
    st.write(f"**Current Required Role:** {selected_row.get('current_required_role') or '—'}")
    st.write(f"**Approval Progress:** {selected_row.get('approval_progress')}")
    st.write(f"**Approval Chain:** {selected_row.get('approval_chain_display')}")
    st.write(f"**Amount:** {selected_row.get('amount')}")
    st.write(f"**Leave Days:** {selected_row.get('leave_days')}")
    st.write(f"**Severity:** {selected_row.get('severity')}")

with c2:
    st.markdown("### Approver Action")
    default_role = selected_row.get("current_required_role") or "MANAGER"

    actor_name = st.text_input("Actor Name")
    actor_role = st.selectbox("Actor Role", ["SUPPORT_L2", "MANAGER", "DIRECTOR", "FINANCE"])
    #actor_role = st.text_input("Actor Role", value=default_role)
    reject_reason = st.text_area("Reject Reason", value="Does not meet approval criteria")
    b1, b2 = st.columns(2)

    with b1:
        if st.button("Approve Request", use_container_width=True):
            if not actor_name.strip():
                st.error("Actor Name is required.")
            elif not actor_role.strip():
                st.error("Actor Role is required.")
            else:
                try:
                    result = approve_request(
                        selected_request_id,
                        actor_name=actor_name.strip(),
                        actor_role=actor_role.strip()
                    )
                    st.success("Request approved successfully.")
                    st.json(result)
                except Exception as e:
                    st.error(f"Approval failed: {e}")

    with b2:
        if st.button("Reject Request", use_container_width=True):
            if not actor_name.strip():
                st.error("Actor Name is required.")
            elif not actor_role.strip():
                st.error("Actor Role is required.")
            elif not reject_reason.strip():
                st.error("Reject Reason is required.")
            else:
                try:
                    result = reject_request(
                        selected_request_id,
                        actor_name=actor_name.strip(),
                        actor_role=actor_role.strip(),
                        reason=reject_reason.strip()
                    )
                    st.success("Request rejected successfully.")
                    st.json(result)
                except Exception as e:
                    st.error(f"Rejection failed: {e}")

st.divider()

# -----------------------------
# Pending-only section
# -----------------------------
st.subheader("Pending Approval Requests")

pending_df = df[df["state"].astype(str).str.upper().isin(["PENDING", "SUBMITTED", "IN_REVIEW"])].copy()

if pending_df.empty:
    st.info("There are no pending approval requests.")
else:
    pending_df["approval_chain_display"] = pending_df.apply(approval_chain_display, axis=1)
    pending_df["approval_progress"] = pending_df.apply(approval_progress_display, axis=1)
    pending_df["current_approver"] = pending_df.apply(current_approver_display, axis=1)

    st.dataframe(
        pending_df[
            [
                "id",
                "title",
                "request_type",
                "state",
                "current_approver",
                "approval_progress",
                "approval_chain_display",
                "created_by",
                "created_at",
            ]
        ],
        use_container_width=True,
        hide_index=True
    )