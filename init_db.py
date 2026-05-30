import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

BASE_DIR    = Path(__file__).parent
DB_PATH     = BASE_DIR / "library.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
CSV_PATH    = BASE_DIR / "database" / "books_dataset.csv"

LOAN_PERIOD_DAYS = 14


def create_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print("[OK] Schema created")


def import_books_from_csv(conn):
    df = pd.read_csv(CSV_PATH)
    cursor = conn.cursor()

    for cat in df["category"].dropna().unique():
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    cursor.execute("SELECT category_id, name FROM categories")
    cat_map = {name: cid for cid, name in cursor.fetchall()}

    inserted, skipped = 0, 0
    for _, row in df.iterrows():
        try:
            cursor.execute(
                "INSERT INTO books (title, author, category_id, year_published, total_copies, available_copies) VALUES (?, ?, ?, ?, ?, ?)",
                (row["title"], row["author"], cat_map.get(row["category"]), int(row["year_published"]), int(row["total_copies"]), int(row["total_copies"])),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    print(f"[OK] Imported {inserted} books ({skipped} skipped)")


def seed_sample_members(conn):
    members = [
        ("Ahmad bin Abdullah", "ahmad@gmail.com",    "0123456789"),
        ("Siti Nurhaliza",     "siti@hotmail.com",   "0198765432"),
        ("Tan Wei Ming",       "tan.wm@hotmail.com", "0167891234"),
        ("Priya Sharma",       "priya.s@gmail.com",  "0145678901"),
        ("Nurul Aisyah",       "nurul.a@hotmail.com","0134567890"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO members (full_name, email, phone) VALUES (?, ?, ?)",
        members,
    )
    conn.commit()
    print(f"[OK] Seeded {len(members)} members")


def seed_sample_borrowings(conn):
    today   = date.today()
    samples = [
        (1,  1, 7,  None),
        (5,  2, 20, None),
        (10, 3, 30, 25),
        (15, 4, 10, None),
        (20, 5, 25, None),
    ]

    cursor = conn.cursor()
    for book_id, member_id, days_borrowed, days_returned in samples:
        borrow_date = today - timedelta(days=days_borrowed)
        due_date    = borrow_date + timedelta(days=LOAN_PERIOD_DAYS)
        return_date = today - timedelta(days=days_returned) if days_returned else None

        if return_date:
            status = "returned"
        elif today > due_date:
            status = "overdue"
        else:
            status = "borrowed"

        cursor.execute(
            "INSERT INTO borrowings (book_id, member_id, borrow_date, due_date, return_date, status) VALUES (?, ?, ?, ?, ?, ?)",
            (book_id, member_id, borrow_date.isoformat(), due_date.isoformat(),
             return_date.isoformat() if return_date else None, status),
        )

        if status != "returned":
            cursor.execute(
                "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
                (book_id,),
            )

    conn.commit()
    print(f"[OK] Seeded {len(samples)} borrowings")


def verify(conn):
    print("\n=== Database Summary ===")
    for table in ("categories", "books", "members", "borrowings"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<14} : {count} rows")


def main():
    reset = "--reset" in sys.argv

    if DB_PATH.exists():
        if reset:
            DB_PATH.unlink()
            print(f"[RESET] Removed {DB_PATH.name}")
        else:
            print(f"[!] {DB_PATH.name} already exists. Use --reset to rebuild.")
            return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        create_schema(conn)
        import_books_from_csv(conn)
        seed_sample_members(conn)
        seed_sample_borrowings(conn)
        verify(conn)
        print(f"\nDone. Database ready at: {DB_PATH}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
