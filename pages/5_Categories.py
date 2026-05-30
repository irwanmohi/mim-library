import streamlit as st
import pandas as pd
from db import fetch_all, fetch_one, execute
from utils import render_sidebar, render_footer

st.set_page_config(page_title="Categories - MIM Library", layout="wide")
render_sidebar()
st.title("Book Categories")

if "pending_delete_cat" not in st.session_state:
    st.session_state.pending_delete_cat = None


@st.dialog("Confirm Delete Category")
def confirm_delete_dialog():
    cat = st.session_state.pending_delete_cat
    st.warning(f"Delete category **{cat['name']}**? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Delete", type="primary", use_container_width=True):
        try:
            execute("DELETE FROM categories WHERE category_id = ?", (cat["category_id"],))
            st.session_state.pending_delete_cat = None
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    if c2.button("Cancel", use_container_width=True):
        st.session_state.pending_delete_cat = None
        st.rerun()


if st.session_state.pending_delete_cat:
    confirm_delete_dialog()

tab_list, tab_add, tab_edit = st.tabs(["All Categories", "Add Category", "Rename / Delete"])

with tab_list:
    cats = fetch_all("""
        SELECT c.name AS Category,
               COUNT(b.book_id) AS Books,
               COALESCE(SUM(b.total_copies), 0) AS "Total Copies",
               COALESCE(SUM(b.available_copies), 0) AS "Available Copies"
        FROM categories c
        LEFT JOIN books b ON b.category_id = c.category_id
        GROUP BY c.category_id, c.name
        ORDER BY c.name
    """)

    if cats:
        st.dataframe(pd.DataFrame(cats), use_container_width=True, hide_index=True)
        st.caption(f"{len(cats)} category/categories")
    else:
        st.info("No categories yet.")

with tab_add:
    st.subheader("Add New Category")
    with st.form("form_add_cat", clear_on_submit=True):
        new_name = st.text_input("Category Name *")
        if st.form_submit_button("Add Category", type="primary"):
            if not new_name.strip():
                st.error("Category name is required.")
            else:
                try:
                    execute("INSERT INTO categories (name) VALUES (?)", (new_name.strip(),))
                    st.success(f"Category '{new_name.strip()}' added.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

with tab_edit:
    st.subheader("Rename or Delete a Category")
    cats_list = fetch_all("SELECT category_id, name FROM categories ORDER BY name")

    if not cats_list:
        st.info("No categories to edit.")
    else:
        options   = {c["name"]: c["category_id"] for c in cats_list}
        chosen    = st.selectbox("Select category", list(options.keys()), key="edit_cat_select")
        cat_id    = options[chosen]

        book_count = fetch_one(
            "SELECT COUNT(*) AS n FROM books WHERE category_id = ?", (cat_id,)
        )["n"]
        st.caption(f"Books in this category: **{book_count}**")

        with st.form("form_rename_cat"):
            new_name = st.text_input("New Name", value=chosen)
            if st.form_submit_button("Save", type="primary"):
                if not new_name.strip():
                    st.error("Name cannot be empty.")
                else:
                    try:
                        execute(
                            "UPDATE categories SET name = ? WHERE category_id = ?",
                            (new_name.strip(), cat_id)
                        )
                        st.success("Category renamed.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()
        if book_count > 0:
            st.info(f"Cannot delete: {book_count} book(s) are assigned to this category.")
        else:
            if st.button("Delete this category", type="secondary", key="delete_cat_btn"):
                st.session_state.pending_delete_cat = {"category_id": cat_id, "name": chosen}
                st.rerun()

render_footer()
