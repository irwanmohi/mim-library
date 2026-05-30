-- ============================================================
-- Library Management System - Database Schema
-- Engine: SQLite 3
-- ============================================================
-- Tables:
--   1. categories  - book categories (Fiction, Science, etc.)
--   2. books       - book catalogue
--   3. members     - library members
--   4. borrowings  - borrowing records (junction with history)
-- ============================================================

-- Enable foreign key enforcement (SQLite has it OFF by default)
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Table: categories
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- Table: books
--   - available_copies must not exceed total_copies
--   - If a category is deleted, books keep existing (category_id = NULL)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    book_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT    NOT NULL,
    author           TEXT    NOT NULL,
    category_id      INTEGER,
    year_published   INTEGER CHECK (year_published BETWEEN 1000 AND 2100),
    total_copies     INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1
                     CHECK (available_copies >= 0 AND available_copies <= total_copies),
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Table: members
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    member_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    phone       TEXT,
    join_date   DATE    NOT NULL DEFAULT CURRENT_DATE,
    status      TEXT    NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'suspended'))
);

-- ------------------------------------------------------------
-- Table: borrowings
--   - status: 'borrowed' (active), 'returned', 'overdue'
--   - fine_amount calculated as RM1 per day late
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS borrowings (
    borrowing_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id       INTEGER NOT NULL,
    member_id     INTEGER NOT NULL,
    borrow_date   DATE    NOT NULL DEFAULT CURRENT_DATE,
    due_date      DATE    NOT NULL,
    return_date   DATE,
    fine_amount   REAL    NOT NULL DEFAULT 0 CHECK (fine_amount >= 0),
    status        TEXT    NOT NULL DEFAULT 'borrowed'
                  CHECK (status IN ('borrowed', 'returned', 'overdue')),
    FOREIGN KEY (book_id)   REFERENCES books(book_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

-- ------------------------------------------------------------
-- Indexes - improve performance of common queries
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_books_category    ON books(category_id);
CREATE INDEX IF NOT EXISTS idx_books_title       ON books(title);
CREATE INDEX IF NOT EXISTS idx_borrowings_member ON borrowings(member_id);
CREATE INDEX IF NOT EXISTS idx_borrowings_book   ON borrowings(book_id);
CREATE INDEX IF NOT EXISTS idx_borrowings_status ON borrowings(status);
