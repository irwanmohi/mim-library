import streamlit as st
import pandas as pd
from pathlib import Path
from db import fetch_one, fetch_all, execute
from utils import render_sidebar, render_footer

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(
    page_title="MIM Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

execute(
    "UPDATE borrowings SET status = 'overdue' "
    "WHERE status = 'borrowed' AND due_date < date('now')"
)

col_logo, col_title = st.columns([1, 4])
with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=140)
with col_title:
    st.markdown("""
        <h1 style='margin-bottom:0; padding-top:0.4rem;'>MIM Library</h1>
        <p style='color:#888; margin-top:4px;'>Library Management System - Dashboard</p>
    """, unsafe_allow_html=True)
st.divider()

total_titles     = fetch_one("SELECT COUNT(*) AS n FROM books")["n"]
total_copies     = fetch_one("SELECT COALESCE(SUM(total_copies), 0) AS n FROM books")["n"]
available        = fetch_one("SELECT COALESCE(SUM(available_copies), 0) AS n FROM books")["n"]
total_members    = fetch_one("SELECT COUNT(*) AS n FROM members")["n"]
active_loans     = fetch_one("SELECT COUNT(*) AS n FROM borrowings WHERE status='borrowed'")["n"]
overdue_count    = fetch_one("SELECT COUNT(*) AS n FROM borrowings WHERE status='overdue'")["n"]
returned_count   = fetch_one("SELECT COUNT(*) AS n FROM borrowings WHERE status='returned'")["n"]
total_categories = fetch_one("SELECT COUNT(*) AS n FROM categories")["n"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Book Titles",      total_titles)
c2.metric("Total Copies",     total_copies)
c3.metric("Available Copies", available)
c4.metric("Total Members",    total_members)
c5.metric("Active Loans",     active_loans)
c6.metric("Overdue",          overdue_count,
          delta=f"+{overdue_count}" if overdue_count else None,
          delta_color="inverse")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Books by Category")
    cat_data = fetch_all("""
        SELECT c.name AS category, COUNT(*) AS titles, SUM(b.total_copies) AS total_copies
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        GROUP BY c.name
        ORDER BY titles DESC
    """)
    if cat_data:
        df_cat = pd.DataFrame(cat_data).set_index("category")
        st.bar_chart(df_cat["titles"], use_container_width=True)
    else:
        st.info("No books in the system yet.")

with col2:
    st.subheader("Copies Available vs Total")
    avail_data = fetch_all("""
        SELECT c.name AS category,
               SUM(b.available_copies) AS available,
               SUM(b.total_copies) AS total
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        GROUP BY c.name
        ORDER BY total DESC
    """)
    if avail_data:
        df_av = pd.DataFrame(avail_data).set_index("category")
        st.bar_chart(df_av[["available", "total"]], use_container_width=True)
    else:
        st.info("No data available.")

st.divider()

col3, col4 = st.columns([1, 2])

with col3:
    st.subheader("Borrowing Summary")
    summary_data = {
        "Status": ["Borrowed", "Overdue", "Returned"],
        "Count":  [active_loans, overdue_count, returned_count],
    }
    df_sum = pd.DataFrame(summary_data)
    if (active_loans + overdue_count + returned_count) > 0:
        st.bar_chart(df_sum.set_index("Status"), use_container_width=True)
    else:
        st.info("No borrowing records yet.")

    st.markdown("**Statistics**")
    total_loans = active_loans + overdue_count + returned_count
    st.markdown(f"- Total loan records: **{total_loans}**")
    st.markdown(f"- Books on loan: **{active_loans + overdue_count}**")
    st.markdown(f"- Books returned: **{returned_count}**")
    st.markdown(f"- Categories: **{total_categories}**")

with col4:
    st.subheader("Overdue Loans")
    overdue_rows = fetch_all("""
        SELECT m.full_name AS member, b.title AS book,
               br.due_date,
               CAST(julianday('now') - julianday(br.due_date) AS INTEGER) AS days_overdue,
               CAST(julianday('now') - julianday(br.due_date) AS INTEGER) * 1.0 AS fine_rm
        FROM borrowings br
        JOIN books   b ON br.book_id   = b.book_id
        JOIN members m ON br.member_id = m.member_id
        WHERE br.status = 'overdue'
        ORDER BY days_overdue DESC
    """)
    if overdue_rows:
        df_ov = pd.DataFrame(overdue_rows)
        df_ov.columns = ["Member", "Book", "Due Date", "Days Overdue", "Fine (RM)"]
        st.dataframe(df_ov, use_container_width=True, hide_index=True)
    else:
        st.success("No overdue loans!")

st.divider()

st.subheader("Recent Borrowing Activity")
recent = fetch_all("""
    SELECT m.full_name AS member, b.title AS book,
           br.borrow_date, br.due_date, br.status
    FROM borrowings br
    JOIN books   b ON br.book_id   = b.book_id
    JOIN members m ON br.member_id = m.member_id
    ORDER BY br.borrow_date DESC
    LIMIT 10
""")
if recent:
    df_recent = pd.DataFrame(recent)
    df_recent.columns = ["Member", "Book", "Borrow Date", "Due Date", "Status"]
    st.dataframe(df_recent, use_container_width=True, hide_index=True)
else:
    st.info("No borrowing activity yet. Issue a book from the Borrowings page.")

render_footer()
