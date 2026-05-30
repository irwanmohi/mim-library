import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import streamlit as st

DB_PATH = Path(__file__).parent / "library.db"


@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        st.error("Database not found. Run init_db.py first.")
        st.stop()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_all(sql, params=()):
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def fetch_one(sql, params=()):
    conn = get_connection()
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def execute(sql, params=()):
    conn = get_connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    if sql.strip().upper().startswith("INSERT"):
        return cursor.lastrowid
    return cursor.rowcount


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
