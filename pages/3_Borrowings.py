import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db import fetch_all, fetch_one, execute, transaction
from utils import render_sidebar, render_footer

st.set_page_config(page_title="Borrowings - MIM Library", layout="wide")
render_sidebar()
st.title("Borrowings")

LOAN_DAYS    = 14
FINE_PER_DAY = 1.0

if "pending_borrow" not in st.session_state:
    st.session_state.pending_borrow = None
if "borrow_success" not in st.session_state:
    st.session_state.borrow_success = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Active Loans"
if "pending_return" not in st.session_state:
    st.session_state.pending_return = None


@st.dialog("Confirm Book Issue")
def confirm_dialog():
    p = st.session_state.pending_borrow
    st.markdown(f"**Book :** {p['book_title']}")
    st.markdown(f"**Member :** {p['member_name']}")
    st.markdown(f"**Borrow Date :** {p['borrow_date']}")
    st.markdown(f"**Due Date :** {p['due_date']}")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Confirm", type="primary", use_container_width=True):
        try:
            with transaction() as conn:
                conn.execute(
                    "INSERT INTO borrowings (book_id, member_id, borrow_date, due_date, status) VALUES (?, ?, ?, ?, 'borrowed')",
                    (p["book_id"], p["member_id"], p["borrow_date"], p["due_date"])
                )
                conn.execute(
                    "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
                    (p["book_id"],)
                )
            st.session_state.pending_borrow = None
            st.session_state.borrow_success = True
            st.session_state.active_tab = "Active Loans"
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    if c2.button("Cancel", use_container_width=True):
        st.session_state.pending_borrow = None
        st.rerun()


@st.dialog("Confirm Book Return")
def confirm_return_dialog():
    p = st.session_state.pending_return
    st.markdown(f"**Book :** {p['book_title']}")
    st.markdown(f"**Member :** {p['member_name']}")
    st.markdown(f"**Return Date :** {p['return_date']}")
    st.markdown(f"**Days Late :** {p['days_late']}")
    st.markdown(f"**Fine :** RM {p['fine']:.2f}")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Confirm", type="primary", use_container_width=True):
        try:
            with transaction() as conn:
                conn.execute(
                    "UPDATE borrowings SET return_date=?, fine_amount=?, status='returned' WHERE borrowing_id=?",
                    (p["return_date"], p["fine"], p["borrowing_id"])
                )
                conn.execute(
                    "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
                    (p["book_id"],)
                )
            st.session_state.pending_return = None
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    if c2.button("Cancel", use_container_width=True):
        st.session_state.pending_return = None
        st.rerun()


if st.session_state.pending_borrow:
    confirm_dialog()
if st.session_state.pending_return:
    confirm_return_dialog()

if st.session_state.borrow_success:
    st.success("Book issued successfully!")
    st.session_state.borrow_success = False

tab_labels = ["Active Loans", "Borrow Book", "Return Book", "History"]
st.session_state.active_tab = "Active Loans"
tab_active, tab_borrow, tab_return, tab_history = st.tabs(tab_labels)

with tab_active:
    loans = fetch_all("""
        SELECT br.borrowing_id AS id, m.full_name AS member, b.title AS book,
               br.borrow_date, br.due_date, br.status,
               CASE WHEN br.status = 'overdue'
                    THEN CAST(julianday('now') - julianday(br.due_date) AS INTEGER)
                    ELSE 0 END AS days_overdue,
               CASE WHEN br.status = 'overdue'
                    THEN CAST(julianday('now') - julianday(br.due_date) AS INTEGER) * 1.0
                    ELSE 0.0 END AS fine_rm
        FROM borrowings br
        JOIN books b ON br.book_id = b.book_id
        JOIN members m ON br.member_id = m.member_id
        WHERE br.status != 'returned'
        ORDER BY br.status DESC, br.due_date
    """)

    if loans:
        df = pd.DataFrame(loans).drop(columns=["id"])
        df.columns = ["Member", "Book", "Borrow Date", "Due Date", "Status", "Days Overdue", "Fine (RM)"]
        df["Fine (RM)"] = df["Fine (RM)"].apply(lambda x: round(x, 2))

        def highlight_overdue(row):
            if row["Status"] == "overdue":
                return ["background-color: #ffcccc"] * len(row)
            return [""] * len(row)

        st.dataframe(df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        st.caption(f"{len(loans)} active loan(s)")
    else:
        st.info("No active loans.")

with tab_borrow:
    st.subheader("Issue a Book to a Member")

    members     = fetch_all("SELECT member_id, full_name, email FROM members WHERE status = 'active' ORDER BY full_name")
    avail_books = fetch_all("SELECT book_id, title, author, available_copies FROM books WHERE available_copies > 0 ORDER BY title")

    if not members:
        st.warning("No active members. Register a member first.")
    elif not avail_books:
        st.warning("No books available for borrowing.")
    else:
        member_opts = {f"{m['full_name']} ({m['email']})": m["member_id"] for m in members}
        book_opts   = {f"{b['title']} - {b['author']} [{b['available_copies']} copy/copies left]": b["book_id"] for b in avail_books}

        with st.form("form_borrow"):
            chosen_member = st.selectbox("Select Member", list(member_opts.keys()))
            chosen_book   = st.selectbox("Select Book",   list(book_opts.keys()))
            borrow_date   = st.date_input("Borrow Date", value=date.today())
            due_date      = st.date_input("Due Date", value=date.today() + timedelta(days=LOAN_DAYS))

            if st.form_submit_button("Issue Book", type="primary"):
                member_id  = member_opts[chosen_member]
                book_id    = book_opts[chosen_book]
                book_check = fetch_one("SELECT available_copies FROM books WHERE book_id = ?", (book_id,))

                if book_check["available_copies"] < 1:
                    st.error("This book is no longer available.")
                elif due_date <= borrow_date:
                    st.error("Due date must be after borrow date.")
                else:
                    st.session_state.pending_borrow = {
                        "book_id":     book_id,
                        "member_id":   member_id,
                        "book_title":  chosen_book.split(" - ")[0],
                        "member_name": chosen_member.split(" (")[0],
                        "borrow_date": borrow_date.isoformat(),
                        "due_date":    due_date.isoformat(),
                    }
                    st.rerun()

with tab_return:
    st.subheader("Process a Book Return")

    active_loans = fetch_all("""
        SELECT br.borrowing_id, m.full_name, b.title, br.borrow_date, br.due_date, br.status
        FROM borrowings br
        JOIN books b ON br.book_id = b.book_id
        JOIN members m ON br.member_id = m.member_id
        WHERE br.status != 'returned'
        ORDER BY br.due_date
    """)

    if not active_loans:
        st.info("No active loans to return.")
    else:
        loan_opts    = {f"{l['full_name']} - {l['title']} (due: {l['due_date']}) [{l['status'].upper()}]": l["borrowing_id"] for l in active_loans}
        chosen_loan  = st.selectbox("Select loan", list(loan_opts.keys()), key="return_select")
        borrowing_id = loan_opts[chosen_loan]

        loan_detail = fetch_one("""
            SELECT br.*, b.title, b.book_id, m.full_name
            FROM borrowings br
            JOIN books b ON br.book_id = b.book_id
            JOIN members m ON br.member_id = m.member_id
            WHERE br.borrowing_id = ?
        """, (borrowing_id,))

        return_date = st.date_input("Return Date", value=date.today(), key="return_date")
        due         = date.fromisoformat(loan_detail["due_date"])
        days_late   = max(0, (return_date - due).days)
        fine        = days_late * FINE_PER_DAY

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Borrow Date", loan_detail["borrow_date"])
        col_b.metric("Days Late",   days_late)
        col_c.metric("Fine (RM)",   f"RM {fine:.2f}")

        if st.button("Confirm Return", type="primary", key="confirm_return"):
            st.session_state.pending_return = {
                "borrowing_id": borrowing_id,
                "book_id":      loan_detail["book_id"],
                "book_title":   loan_detail["title"],
                "member_name":  loan_detail["full_name"],
                "return_date":  return_date.isoformat(),
                "days_late":    days_late,
                "fine":         fine,
            }
            st.rerun()

with tab_history:
    st.subheader("Full Borrowing History")
    search_h = st.text_input("Search by member name or book title", key="history_search")

    history = fetch_all("""
        SELECT m.full_name AS member, b.title AS book,
               br.borrow_date, br.due_date, br.return_date,
               br.fine_amount AS fine_rm, br.status
        FROM borrowings br
        JOIN books b ON br.book_id = b.book_id
        JOIN members m ON br.member_id = m.member_id
        WHERE (m.full_name LIKE ? OR b.title LIKE ?)
        ORDER BY br.borrow_date DESC
    """, (f"%{search_h}%", f"%{search_h}%"))

    if history:
        df_h = pd.DataFrame(history)
        df_h.columns = ["Member", "Book", "Borrow Date", "Due Date", "Return Date", "Fine (RM)", "Status"]
        st.dataframe(df_h, use_container_width=True, hide_index=True)
        st.caption(f"{len(history)} record(s)")
        st.download_button(
            label="Export to CSV",
            data=df_h.to_csv(index=False).encode("utf-8"),
            file_name="borrowing_history.csv",
            mime="text/csv",
        )
    else:
        st.info("No records found.")

render_footer()
