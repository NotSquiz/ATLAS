"""
ATLAS LLM Cost Tracker

SQLite-based usage logging with budget enforcement.
Implements soft/hard limits and graceful degradation.
"""

import sqlite3
import hashlib
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from contextlib import contextmanager


@dataclass
class UsageRecord:
    """Single API usage record."""
    tier: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    category: str
    confidence: float


@dataclass
class BudgetStatus:
    """Current budget status."""
    daily_spend: float
    monthly_spend: float
    daily_limit: float
    monthly_limit: float

    @property
    def daily_remaining(self) -> float:
        return max(0, self.daily_limit - self.daily_spend)

    @property
    def monthly_remaining(self) -> float:
        return max(0, self.monthly_limit - self.monthly_spend)

    @property
    def can_use_api(self) -> bool:
        return self.monthly_spend < self.monthly_limit

    @property
    def thrifty_mode(self) -> bool:
        """True when approaching budget - prefer local."""
        return self.monthly_spend > (self.monthly_limit * 0.8)


class CostTracker:
    """
    Track LLM usage costs with budget enforcement.

    Budget levels:
    - Soft limit (80%): Enable "thrifty mode" - prefer local
    - Hard limit (100%): API blocked, local-only mode
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS llm_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        query_hash TEXT NOT NULL,
        tier TEXT NOT NULL,
        model TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        cost_usd REAL NOT NULL,
        latency_ms REAL NOT NULL,
        routing_confidence REAL,
        category TEXT,
        escalated BOOLEAN DEFAULT FALSE,
        escalation_reason TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_timestamp ON llm_usage(timestamp);
    CREATE INDEX IF NOT EXISTS idx_tier ON llm_usage(tier);
    CREATE INDEX IF NOT EXISTS idx_date ON llm_usage(DATE(timestamp));

    CREATE TABLE IF NOT EXISTS budget_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        daily_limit_usd REAL DEFAULT 0.33,
        monthly_limit_usd REAL DEFAULT 10.00,
        soft_limit_pct REAL DEFAULT 0.80,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    INSERT OR IGNORE INTO budget_config (id) VALUES (1);
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "cost_tracker.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript(self.SCHEMA)

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_usage(self, record: UsageRecord, query: str = "") -> None:
        """Log an API usage record."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16] if query else ""

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO llm_usage
                (query_hash, tier, model, input_tokens, output_tokens,
                 cost_usd, latency_ms, routing_confidence, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_hash, record.tier, record.model,
                record.input_tokens, record.output_tokens,
                record.cost_usd, record.latency_ms,
                record.confidence, record.category
            ))

    def get_budget_status(self) -> BudgetStatus:
        """Get current budget status."""
        with self._get_conn() as conn:
            # Get config
            config = conn.execute(
                "SELECT daily_limit_usd, monthly_limit_usd FROM budget_config WHERE id = 1"
            ).fetchone()

            # Get daily spend
            daily = conn.execute("""
                SELECT COALESCE(SUM(cost_usd), 0) as total
                FROM llm_usage WHERE DATE(timestamp) = DATE('now')
            """).fetchone()['total']

            # Get monthly spend
            monthly = conn.execute("""
                SELECT COALESCE(SUM(cost_usd), 0) as total
                FROM llm_usage
                WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
            """).fetchone()['total']

            return BudgetStatus(
                daily_spend=daily,
                monthly_spend=monthly,
                daily_limit=config['daily_limit_usd'],
                monthly_limit=config['monthly_limit_usd'],
            )

    def set_budget(self, daily: Optional[float] = None, monthly: Optional[float] = None):
        """Update budget limits."""
        with self._get_conn() as conn:
            if daily is not None:
                conn.execute(
                    "UPDATE budget_config SET daily_limit_usd = ? WHERE id = 1",
                    (daily,)
                )
            if monthly is not None:
                conn.execute(
                    "UPDATE budget_config SET monthly_limit_usd = ? WHERE id = 1",
                    (monthly,)
                )

    def get_daily_summary(self, days: int = 7) -> list[dict]:
        """Get daily usage summary for last N days."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    DATE(timestamp) as date,
                    tier,
                    COUNT(*) as requests,
                    SUM(cost_usd) as cost,
                    AVG(latency_ms) as avg_latency
                FROM llm_usage
                WHERE timestamp > datetime('now', ? || ' days')
                GROUP BY DATE(timestamp), tier
                ORDER BY date DESC, tier
            """, (f"-{days}",)).fetchall()

            return [dict(row) for row in rows]


# Singleton instance
_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get singleton cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
