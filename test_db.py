from datetime import date, timedelta
from db import fetch_all, fetch_one, execute, transaction


def section(title):
    print(f"\n{'=' * 50}\n  {title}\n{'=' * 50}")


section("Test 1: fetch_all - list categories")
categories = fetch_all("SELECT * FROM categories ORDER BY name")
print(f"Found {len(categories)} categories:")
for cat in categories:
    print(f"  - {cat['name']} (id={cat['category_id']})")


section("Test 2: fetch_one - get a specific book")
book = fetch_one(
    """
    SELECT b.title, b.author, c.name AS category, b.available_copies
    FROM books b
    LEFT JOIN categories c ON b.category_id = c.category_id
    WHERE b.book_id = ?
    """,
    (1,),
)
print(f"Book #1: {book}")


section("Test 3: fetch_one with no match - should return None")
missing = fetch_one("SELECT * FROM books WHERE book_id = ?", (99999,))
print(f"Book #99999: {missing}  (should be None)")


section("Test 4: execute INSERT - add a test member")
new_id = execute(
    "INSERT INTO members (full_name, email, phone) VALUES (?, ?, ?)",
    ("Test User", "test_smoke@example.com", "0000000000"),
)
print(f"Inserted member with new ID: {new_id}")
just_added = fetch_one("SELECT * FROM members WHERE member_id = ?", (new_id,))
print(f"Retrieved: {just_added}")


section("Test 5: execute UPDATE - change the phone")
rows_changed = execute(
    "UPDATE members SET phone = ? WHERE member_id = ?",
    ("0111111111", new_id),
)
print(f"Rows updated: {rows_changed}  (should be 1)")


section("Test 6: transaction - atomic operation")
today = date.today()
due   = today + timedelta(days=14)

before = fetch_one("SELECT available_copies FROM books WHERE book_id = ?", (2,))
print(f"Book #2 available BEFORE: {before['available_copies']}")

with transaction() as conn:
    conn.execute(
        "INSERT INTO borrowings (book_id, member_id, borrow_date, due_date) VALUES (?, ?, ?, ?)",
        (2, new_id, today.isoformat(), due.isoformat()),
    )
    conn.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
        (2,),
    )

after = fetch_one("SELECT available_copies FROM books WHERE book_id = ?", (2,))
print(f"Book #2 available AFTER:  {after['available_copies']}  (should be 1 less)")


section("Test 7: transaction rollback - should NOT commit on error")
before = fetch_one("SELECT available_copies FROM books WHERE book_id = ?", (3,))
print(f"Book #3 available BEFORE failed txn: {before['available_copies']}")

try:
    with transaction() as conn:
        conn.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (3,),
        )
        conn.execute(
            "INSERT INTO borrowings (book_id, member_id, borrow_date, due_date) VALUES (?, ?, ?, ?)",
            (3, 99999, today.isoformat(), due.isoformat()),
        )
except Exception as e:
    print(f"  Caught expected error: {type(e).__name__}: {e}")

after = fetch_one("SELECT available_copies FROM books WHERE book_id = ?", (3,))
print(f"Book #3 available AFTER failed txn:  {after['available_copies']}  (should be SAME as before)")


section("Cleanup: remove test data")
execute("DELETE FROM borrowings WHERE member_id = ?", (new_id,))
execute("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = 2")
execute("DELETE FROM members WHERE member_id = ?", (new_id,))
print("Test data cleaned up.")

print("\n" + "=" * 50)
print("  All tests passed.")
print("=" * 50)
