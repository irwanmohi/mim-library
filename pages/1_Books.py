import streamlit as st
import pandas as pd
from db import fetch_all, fetch_one, execute
from utils import render_sidebar, render_footer

st.set_page_config(page_title="Books - MIM Library", layout="wide")
render_sidebar()
st.title("Books Catalogue")

tab_browse, tab_add, tab_edit = st.tabs(["Browse Books", "Add Book", "Edit / Delete"])

with tab_browse:
    col_s, col_c = st.columns([3, 1])
    search = col_s.text_input("Search by title or author", key="book_search")

    categories = fetch_all("SELECT * FROM categories ORDER BY name")
    cat_options = {"All": None} | {c["name"]: c["category_id"] for c in categories}
    selected_cat = col_c.selectbox("Category", list(cat_options.keys()), key="book_cat")

    sql = """
        SELECT b.title AS Title, b.author AS Author,
               c.name AS Category, b.year_published AS Year,
               b.available_copies AS Available, b.total_copies AS Total
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        WHERE (b.title LIKE ? OR b.author LIKE ?)
    """
    params = [f"%{search}%", f"%{search}%"]

    if cat_options[selected_cat]:
        sql += " AND b.category_id = ?"
        params.append(cat_options[selected_cat])

    sql += " ORDER BY b.title"
    books = fetch_all(sql, tuple(params))

    st.caption(f"{len(books)} book(s) found")
    if books:
        df = pd.DataFrame(books)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            label="Export to CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="books_export.csv",
            mime="text/csv",
        )
    else:
        st.info("No books match your search.")

with tab_add:
    st.subheader("Add New Book")
    categories = fetch_all("SELECT * FROM categories ORDER BY name")
    cat_map = {c["name"]: c["category_id"] for c in categories}

    with st.form("form_add_book", clear_on_submit=True):
        title  = st.text_input("Title *")
        author = st.text_input("Author *")
        cat    = st.selectbox("Category", list(cat_map.keys()))
        year   = st.number_input("Year Published", min_value=1000, max_value=2100, value=2020, step=1)
        copies = st.number_input("Number of Copies", min_value=1, value=1, step=1)

        if st.form_submit_button("Add Book", type="primary"):
            if not title.strip() or not author.strip():
                st.error("Title and Author are required.")
            else:
                try:
                    execute(
                        "INSERT INTO books (title, author, category_id, year_published, total_copies, available_copies) VALUES (?, ?, ?, ?, ?, ?)",
                        (title.strip(), author.strip(), cat_map[cat], int(year), int(copies), int(copies))
                    )
                    st.success(f"'{title}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

with tab_edit:
    st.subheader("Edit or Delete a Book")
    books_list = fetch_all("SELECT book_id, title, author FROM books ORDER BY title")

    if not books_list:
        st.info("No books in the system.")
    else:
        options = {f"{b['title']} - {b['author']}": b["book_id"] for b in books_list}
        chosen  = st.selectbox("Select a book", list(options.keys()), key="edit_book_select")
        book_id = options[chosen]

        book = fetch_one("""
            SELECT b.*, c.name AS category_name
            FROM books b
            LEFT JOIN categories c ON b.category_id = c.category_id
            WHERE b.book_id = ?
        """, (book_id,))

        currently_borrowed = book["total_copies"] - book["available_copies"]
        e1, e2, e3 = st.columns(3)
        e1.metric("Total Copies",     book["total_copies"])
        e2.metric("Available Copies", book["available_copies"])
        e3.metric("Currently Borrowed", currently_borrowed)

        categories  = fetch_all("SELECT * FROM categories ORDER BY name")
        cat_map     = {c["name"]: c["category_id"] for c in categories}
        cat_names   = list(cat_map.keys())
        current_idx = cat_names.index(book["category_name"]) if book["category_name"] in cat_names else 0

        with st.form("form_edit_book"):
            title  = st.text_input("Title", value=book["title"])
            author = st.text_input("Author", value=book["author"])
            cat    = st.selectbox("Category", cat_names, index=current_idx)
            year   = st.number_input("Year Published", min_value=1000, max_value=2100,
                                     value=book["year_published"] or 2000, step=1)
            total  = st.number_input("Total Copies", min_value=currently_borrowed, value=book["total_copies"], step=1,
                                     help=f"Minimum {currently_borrowed} (currently on loan)")
            save_btn = st.form_submit_button("Save Changes", type="primary")

        if save_btn:
            new_available = int(total) - currently_borrowed
            execute(
                "UPDATE books SET title=?, author=?, category_id=?, year_published=?, total_copies=?, available_copies=? WHERE book_id=?",
                (title.strip(), author.strip(), cat_map[cat], int(year), int(total), new_available, book_id)
            )
            st.success("Book updated successfully!")
            st.rerun()

        st.divider()
        if st.button("Delete this book", type="secondary", key="delete_book_btn"):
            if currently_borrowed > 0:
                st.error("Cannot delete: this book still has active loans.")
            else:
                execute("DELETE FROM books WHERE book_id = ?", (book_id,))
                st.success("Book deleted.")
                st.rerun()

render_footer()
