import streamlit as st
import pandas as pd
from db import fetch_all, execute
from utils import render_sidebar, render_footer

st.set_page_config(page_title="Import CSV - MIM Library", layout="wide")

render_sidebar()

st.title("Import Books from CSV")

st.info("Upload a CSV file to bulk-import books into MIM Library.")

with st.expander("Expected CSV format"):
    st.markdown("""
| title | author | category | year_published | total_copies |
|-------|--------|----------|---------------|--------------|
| Salina | A. Samad Said | Sastera | 1961 | 3 |
| Tombiruo: Penunggu Rimba | Ramlee Awang Murshid | Thriller | 2001 | 5 |

- `title`, `author`, `category`, `year_published`, `total_copies` - **required**
""")

uploaded = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
    st.caption(f"Total rows in file: {len(df)}")

    required_cols = {"title", "author", "category", "year_published", "total_copies"}
    missing_cols  = required_cols - set(df.columns)

    if missing_cols:
        st.error(f"Missing required columns: {', '.join(sorted(missing_cols))}")
    else:
        st.success("CSV format looks correct. Ready to import.")

        if st.button("Import into MIM Library", type="primary"):
            unique_cats = df["category"].dropna().unique()
            for cat in unique_cats:
                execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (str(cat),))

            cats    = fetch_all("SELECT category_id, name FROM categories")
            cat_map = {c["name"]: c["category_id"] for c in cats}

            inserted, skipped = 0, 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    copies = int(row["total_copies"])
                    execute(
                        """INSERT INTO books
                           (title, author, category_id, year_published,
                            total_copies, available_copies)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            str(row["title"]),
                            str(row["author"]),
                            cat_map.get(str(row["category"])),
                            int(row["year_published"]),
                            copies,
                            copies,
                        )
                    )
                    inserted += 1
                except Exception as e:
                    skipped += 1
                    errors.append(f"Row {idx + 2}: {e}")

            st.success(f"Import complete - {inserted} book(s) added, {skipped} skipped.")

            if errors:
                with st.expander(f"Show {skipped} skipped row(s)"):
                    for err in errors:
                        st.text(err)

            st.rerun()

render_footer()
