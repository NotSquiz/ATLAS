"""Shared fixtures for Baby Brains tests."""

import sqlite3

import pytest

from atlas.babybrains.db import init_bb_tables, run_content_migration


@pytest.fixture
def bb_conn(tmp_path):
    """Create a test database with BB tables initialized."""
    db_path = tmp_path / "test_bb.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Init the main ATLAS schema tables we depend on (minimal)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS semantic_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            importance REAL DEFAULT 0.5,
            memory_type TEXT DEFAULT 'general',
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP
        );
    """)
    conn.commit()

    # Init BB tables
    init_bb_tables(conn)

    # Run content production migration to add new columns
    run_content_migration(conn)

    yield conn
    conn.close()
