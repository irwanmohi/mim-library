import streamlit as st
import pandas as pd
from db import fetch_all, fetch_one, execute
from utils import render_sidebar, render_footer

st.set_page_config(page_title="Members - MIM Library", layout="wide")
render_sidebar()
st.title("Library Members")

if "pending_register" not in st.session_state:
    st.session_state.pending_register = None
if "pending_edit" not in st.session_state:
    st.session_state.pending_edit = None


@st.dialog("Confirm Registration")
def confirm_register_dialog():
    p = st.session_state.pending_register
    st.markdown(f"**Full Name :** {p['name']}")
    st.markdown(f"**Email :** {p['email']}")
    st.markdown(f"**Phone :** {p['phone'] or '-'}")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Confirm", type="primary", use_container_width=True):
        try:
            execute(
                "INSERT INTO members (full_name, email, phone) VALUES (?, ?, ?)",
                (p["name"], p["email"], p["phone"])
            )
            st.session_state.pending_register = None
            st.switch_page("pages/2_Members.py")
        except Exception as e:
            st.error(f"Error: {e}")
    if c2.button("Cancel", use_container_width=True):
        st.session_state.pending_register = None
        st.rerun()


@st.dialog("Confirm Update")
def confirm_edit_dialog():
    p = st.session_state.pending_edit
    st.markdown(f"**Full Name :** {p['name']}")
    st.markdown(f"**Email :** {p['email']}")
    st.markdown(f"**Phone :** {p['phone'] or '-'}")
    st.markdown(f"**Status :** {p['status']}")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Confirm", type="primary", use_container_width=True):
        try:
            execute(
                "UPDATE members SET full_name=?, email=?, phone=?, status=? WHERE member_id=?",
                (p["name"], p["email"], p["phone"], p["status"], p["member_id"])
            )
            st.session_state.pending_edit = None
            st.switch_page("pages/2_Members.py")
        except Exception as e:
            st.error(f"Error: {e}")
    if c2.button("Cancel", use_container_width=True):
        st.session_state.pending_edit = None
        st.rerun()


if st.session_state.pending_register:
    confirm_register_dialog()
if st.session_state.pending_edit:
    confirm_edit_dialog()

tab_list, tab_add, tab_edit = st.tabs(["Member List", "Register Member", "Edit Member"])

with tab_list:
    col_s, col_f = st.columns([3, 1])
    search        = col_s.text_input("Search by name or email", key="member_search")
    status_filter = col_f.selectbox("Status", ["All", "active", "suspended"], key="member_status")

    sql    = "SELECT full_name AS Name, email AS Email, phone AS Phone, join_date AS \"Join Date\", status AS Status FROM members WHERE (full_name LIKE ? OR email LIKE ?)"
    params = [f"%{search}%", f"%{search}%"]

    if status_filter != "All":
        sql += " AND status = ?"
        params.append(status_filter)

    sql += " ORDER BY full_name"
    members = fetch_all(sql, tuple(params))

    st.caption(f"{len(members)} member(s) found")
    if members:
        df_members = pd.DataFrame(members)

        def colour_status(val):
            if val == "active":
                return "background-color: #1a472a; color: #6fcf97;"
            elif val == "suspended":
                return "background-color: #4a1a1a; color: #eb5757;"
            return ""

        st.dataframe(
            df_members.style.map(colour_status, subset=["Status"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No members found.")

with tab_add:
    st.subheader("Register New Member")
    with st.form("form_add_member", clear_on_submit=True):
        name  = st.text_input("Full Name *")
        email = st.text_input("Email *")
        phone = st.text_input("Phone Number")

        if st.form_submit_button("Register", type="primary"):
            if not name.strip() or not email.strip():
                st.error("Full Name and Email are required.")
            else:
                st.session_state.pending_register = {
                    "name":  name.strip(),
                    "email": email.strip(),
                    "phone": phone.strip() or None,
                }
                st.rerun()

with tab_edit:
    st.subheader("Edit Member Details")
    members_list = fetch_all("SELECT member_id, full_name, email FROM members ORDER BY full_name")

    if not members_list:
        st.info("No members registered yet.")
    else:
        options   = {f"{m['full_name']} ({m['email']})": m["member_id"] for m in members_list}
        chosen    = st.selectbox("Select member", list(options.keys()), key="edit_member_select")
        member_id = options[chosen]
        member    = fetch_one("SELECT * FROM members WHERE member_id = ?", (member_id,))

        loan_summary = fetch_one("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status != 'returned' THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) AS overdue
            FROM borrowings WHERE member_id = ?
        """, (member_id,))

        s1, s2, s3 = st.columns(3)
        s1.metric("Total Loans",  loan_summary["total"])
        s2.metric("Active Loans", loan_summary["active"])
        s3.metric("Overdue",      loan_summary["overdue"])
        st.divider()

        with st.form("form_edit_member"):
            name   = st.text_input("Full Name", value=member["full_name"])
            email  = st.text_input("Email",     value=member["email"])
            phone  = st.text_input("Phone",     value=member["phone"] or "")
            status = st.selectbox("Status", ["active", "suspended"],
                                  index=0 if member["status"] == "active" else 1)

            if st.form_submit_button("Save Changes", type="primary"):
                st.session_state.pending_edit = {
                    "member_id": member_id,
                    "name":      name.strip(),
                    "email":     email.strip(),
                    "phone":     phone.strip() or None,
                    "status":    status,
                }
                st.rerun()

render_footer()
