# MIM Library Management System

A Python-based library management system built with Streamlit, using SQLite as the database.

🔗 **Live Demo:** https://mim-library-foqlfzh6ps2xyrpderp3dv.streamlit.app/

---

**Subject:** BIT1034 Advanced Programming
**Institution:** Malaysia University of Science and Technology

| Name | Student ID |
|------|------------|
| Mohd Irwan bin Mohi | B25090011 |
| Izzat Dhiyauddin bin Zainuddin | B25080294 |

---

## Features

- **Dashboard** — Key metrics, charts by category, overdue loans summary
- **Books** — Browse, add, edit, and delete books; filter by category; export to CSV
- **Members** — Register, view, and edit library members
- **Borrowings** — Issue books, process returns, track active loans and history; export history to CSV
- **Categories** — Add, rename, and delete book categories with full CRUD
- **Import CSV** — Bulk import books from a CSV file

---

## Requirements

- Python 3.9 or later
- pip (Python package manager)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/irwanmohi/mim-library.git
cd mim-library
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
```

Activate the virtual environment:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialise the database

Run this once to create the SQLite database and load sample data:

```bash
python init_db.py
```

This will create `library.db` with sample books, members, and categories.

---

## Running the App

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## Usage Guide

### Dashboard
The home page shows an overview of the library — total books, members, active loans, and overdue counts. Charts display books by category and borrowing status.

### Books
- **Browse Books** — Search by title or author, filter by category. Use the **Export to CSV** button to download the current results.
- **Add Book** — Fill in the title, author, category, year, and number of copies.
- **Edit / Delete** — Select a book to update its details or delete it. Editing the total copy count automatically recalculates the available copies based on how many are currently on loan. Deletion is blocked if the book has active loans.

### Members
- **Member List** — View all members with search and status filter (active/suspended). Active members are highlighted green, suspended members in red.
- **Register Member** — Add a new member with name, email, and phone number. A confirmation dialog appears before saving.
- **Edit Member** — Update member details or change their status. A confirmation dialog appears before saving.

### Borrowings
- **Active Loans** — View all currently borrowed and overdue books. Overdue rows are highlighted in red.
- **Borrow Book** — Select a member and a book to issue. A confirmation dialog appears before saving.
- **Return Book** — Select an active loan, set the return date, and confirm. Fine is calculated automatically at RM 1.00 per day late.
- **History** — Full borrowing history searchable by member name or book title. Use the **Export to CSV** button to download the records.

### Categories
- **All Categories** — View all categories with the number of books, total copies, and available copies per category.
- **Add Category** — Create a new category.
- **Rename / Delete** — Rename an existing category or delete it. Deletion is blocked if any books are assigned to that category.

### Import CSV
Upload a `.csv` file to bulk-import books. The file must contain these columns:

| title | author | category | year_published | total_copies |
|-------|--------|----------|---------------|--------------|

New categories in the CSV will be created automatically.

---

## Project Structure

```
mim-library/
├── app.py                  # Main dashboard page
├── init_db.py              # Database initialisation script
├── db.py                   # Database connection and query helpers
├── utils.py                # Shared UI components (sidebar, footer)
├── test_db.py              # Smoke tests for db.py functions
├── requirements.txt        # Python dependencies
├── pages/
│   ├── 1_Books.py          # Books management page
│   ├── 2_Members.py        # Members management page
│   ├── 3_Borrowings.py     # Borrowings page
│   ├── 4_Import_CSV.py     # CSV import page
│   └── 5_Categories.py     # Categories management page
├── database/
│   ├── schema.sql          # Database schema
│   └── books_dataset.csv   # Sample Malaysian books dataset
└── assets/
    └── logo.png            # MIM Library logo
```

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3 | Core programming language |
| Streamlit | Web application framework |
| SQLite | Local database |
| pandas | Data manipulation and display |

---

*Mohd Irwan bin Mohi (B25090011) & Izzat Dhiyauddin bin Zainuddin (B25080294) | MIM Library &copy; 2026*
