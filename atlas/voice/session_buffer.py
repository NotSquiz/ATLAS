"""
Session Buffer for Voice Pipeline

Maintains a rolling buffer of recent voice exchanges for LLM context injection.
SQLite-backed for persistence across restarts.

Usage:
    from atlas.voice.session_buffer import SessionBuffer

    buffer = SessionBuffer()
    buffer.add_exchange("what's my status", "GREEN. 7.2 hours. Ready.", "health")

    # Get formatted context for LLM
    context = buffer.format_for_llm()  # Returns last 5 exchanges
"""

import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Exchange:
    """A single voice exchange."""
    timestamp: float
    user_text: str
    atlas_response: str
    intent_type: str

    def is_stale(self, ttl_minutes: int = 10) -> bool:
        """Check if exchange is older than TTL."""
        age = time.time() - self.timestamp
        return age > (ttl_minutes * 60)

    @property
    def age_seconds(self) -> float:
        """Get age of exchange in seconds."""
        return time.time() - self.timestamp


class SessionBuffer:
    """
    Rolling buffer of recent voice exchanges.

    - Stores last 5 exchanges
    - 10-minute TTL per exchange
    - Persisted to SQLite for crash recovery
    - Uses main atlas.db (not separate file)
    """

    MAX_EXCHANGES = 5
    TTL_MINUTES = 10

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SessionBuffer.

        Args:
            db_path: Path to SQLite database (default: ~/.atlas/atlas.db)
        """
        if db_path is None:
            db_path = os.path.expanduser("~/.atlas/atlas.db")
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        """Create session_buffer table if not exists."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                user_text TEXT NOT NULL,
                atlas_response TEXT NOT NULL,
                intent_type TEXT DEFAULT 'query',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_buffer_ts ON session_buffer(timestamp DESC)"
        )
        conn.commit()
        conn.close()

    def add_exchange(
        self,
        user_text: str,
        atlas_response: str,
        intent_type: str = "query",
    ) -> None:
        """
        Add an exchange to the buffer.

        Automatically prunes old exchanges to keep buffer at MAX_EXCHANGES.

        Args:
            user_text: User's voice input
            atlas_response: ATLAS's response
            intent_type: Type of intent (e.g., "health", "pain", "workout")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Insert new exchange
            conn.execute("""
                INSERT INTO session_buffer (timestamp, user_text, atlas_response, intent_type)
                VALUES (?, ?, ?, ?)
            """, (time.time(), user_text, atlas_response, intent_type))

            # Prune old exchanges (keep only MAX_EXCHANGES)
            conn.execute("""
                DELETE FROM session_buffer WHERE id NOT IN (
                    SELECT id FROM session_buffer ORDER BY timestamp DESC LIMIT ?
                )
            """, (self.MAX_EXCHANGES,))

            # Prune stale exchanges (older than TTL)
            cutoff = time.time() - (self.TTL_MINUTES * 60)
            conn.execute("DELETE FROM session_buffer WHERE timestamp < ?", (cutoff,))

            conn.commit()
            logger.debug(f"Added exchange: {intent_type} - {user_text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to add exchange: {e}")
        finally:
            conn.close()

    def get_context(self, max_exchanges: int = 5) -> list[Exchange]:
        """
        Get recent non-stale exchanges for LLM context.

        Args:
            max_exchanges: Maximum exchanges to return

        Returns:
            List of Exchange in chronological order (oldest first)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cutoff = time.time() - (self.TTL_MINUTES * 60)

        try:
            cursor = conn.execute("""
                SELECT timestamp, user_text, atlas_response, intent_type
                FROM session_buffer
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (cutoff, max_exchanges))

            exchanges = [
                Exchange(
                    timestamp=row["timestamp"],
                    user_text=row["user_text"],
                    atlas_response=row["atlas_response"],
                    intent_type=row["intent_type"],
                )
                for row in cursor.fetchall()
            ]

            # Return in chronological order (oldest first)
            return list(reversed(exchanges))
        finally:
            conn.close()

    def format_for_llm(self) -> str:
        """
        Format buffer as context for LLM injection.

        Returns:
            Formatted string of recent exchanges, or empty string if no context
        """
        exchanges = self.get_context()

        if not exchanges:
            return ""

        lines = ["Recent conversation:"]
        for ex in exchanges:
            lines.append(f"User: {ex.user_text}")
            lines.append(f"Atlas: {ex.atlas_response}")

        return "\n".join(lines)

    def last_topic(self) -> Optional[str]:
        """
        Get the intent type of the most recent exchange.

        Useful for pronoun resolution ("it", "that", etc.).

        Returns:
            Intent type string or None if buffer empty
        """
        exchanges = self.get_context(max_exchanges=1)
        if exchanges:
            return exchanges[-1].intent_type
        return None

    def clear(self) -> None:
        """Clear all exchanges (for testing or reset)."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM session_buffer")
        conn.commit()
        conn.close()
        logger.info("Session buffer cleared")


# Convenience function
def get_session_buffer() -> SessionBuffer:
    """Get a session buffer instance."""
    return SessionBuffer()
