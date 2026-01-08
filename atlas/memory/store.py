"""
ATLAS Memory Store

SQLite-based memory system with:
- sqlite-vec for vector similarity search
- FTS5 for full-text search
- Hybrid RRF ranking (60% vector, 40% FTS)
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import sqlite_vec
    SQLITE_VEC_AVAILABLE = True
except ImportError:
    SQLITE_VEC_AVAILABLE = False


@dataclass
class Memory:
    """A memory entry."""
    id: int
    content: str
    importance: float
    memory_type: str
    source: Optional[str]
    created_at: datetime
    access_count: int


@dataclass
class SearchResult:
    """A search result with score."""
    memory: Memory
    score: float
    match_type: str  # 'vector', 'fts', 'hybrid'


class MemoryStore:
    """
    SQLite-based memory store with vector and full-text search.

    Usage:
        store = MemoryStore()  # Uses default ~/.atlas/atlas.db
        store.init_db()

        # Add a memory (auto-generates embedding if not provided)
        store.add_memory("User prefers morning workouts", importance=0.8)

        # Search memories
        results = store.search_hybrid("workout preferences", limit=5)
    """

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            db_path = Path.home() / ".atlas" / "atlas.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

            # Performance pragmas
            self._conn.execute("PRAGMA mmap_size = 268435456")  # 256MB mmap
            self._conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            self._conn.execute("PRAGMA temp_store = MEMORY")

            # Load sqlite-vec extension if available
            if SQLITE_VEC_AVAILABLE:
                self._conn.enable_load_extension(True)
                sqlite_vec.load(self._conn)
                self._conn.enable_load_extension(False)

        return self._conn

    def init_db(self) -> None:
        """Initialize database with schema."""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema = schema_path.read_text()
        self.conn.executescript(schema)
        self.conn.commit()

    def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        memory_type: str = "general",
        source: Optional[str] = None,
        embedding: Optional[list[float]] = None,
    ) -> int:
        """
        Add a memory to the store.

        Args:
            content: The memory content
            importance: Importance score 0-1 (default 0.5)
            memory_type: Type of memory ('general', 'fact', 'preference', 'event')
            source: Where this memory came from
            embedding: Optional 384-dim embedding vector (auto-generated if not provided)

        Returns:
            The ID of the inserted memory
        """
        # Auto-generate embedding if not provided and sqlite-vec is available
        if embedding is None and SQLITE_VEC_AVAILABLE:
            try:
                from .embeddings import get_embedder
                embedding = get_embedder().embed(content).embedding
            except ImportError:
                pass  # Graceful degradation if embeddings not available

        cursor = self.conn.execute(
            """
            INSERT INTO semantic_memory (content, importance, memory_type, source)
            VALUES (?, ?, ?, ?)
            """,
            (content, importance, memory_type, source),
        )
        memory_id = cursor.lastrowid

        # Add embedding if available and sqlite-vec is loaded
        if embedding is not None and SQLITE_VEC_AVAILABLE:
            self.conn.execute(
                "INSERT INTO vec_semantic (memory_id, embedding) VALUES (?, ?)",
                (memory_id, sqlite_vec.serialize_float32(embedding)),
            )

        self.conn.commit()
        return memory_id

    def search_fts(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search memories using FTS5 full-text search."""
        cursor = self.conn.execute(
            """
            SELECT
                m.id, m.content, m.importance, m.memory_type,
                m.source, m.created_at, m.access_count,
                bm25(fts_memory) as score
            FROM fts_memory
            JOIN semantic_memory m ON fts_memory.rowid = m.id
            WHERE fts_memory MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        )

        results = []
        for row in cursor.fetchall():
            memory = Memory(
                id=row["id"],
                content=row["content"],
                importance=row["importance"],
                memory_type=row["memory_type"],
                source=row["source"],
                created_at=datetime.fromisoformat(row["created_at"]),
                access_count=row["access_count"],
            )
            results.append(SearchResult(
                memory=memory,
                score=abs(row["score"]),  # BM25 returns negative scores
                match_type="fts",
            ))

        return results

    def search_vector(
        self,
        embedding: list[float],
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search memories using vector similarity."""
        if not SQLITE_VEC_AVAILABLE:
            return []

        # Two-phase query: vector search first (fast), then fetch metadata
        # This avoids the JOIN overhead during the KNN search
        cursor = self.conn.execute(
            """
            SELECT memory_id, distance
            FROM vec_semantic
            WHERE embedding MATCH ? AND k = ?
            """,
            (sqlite_vec.serialize_float32(embedding), limit),
        )
        vec_results = cursor.fetchall()

        if not vec_results:
            return []

        # Fetch memory metadata for matched IDs
        memory_ids = [r["memory_id"] for r in vec_results]
        distances = {r["memory_id"]: r["distance"] for r in vec_results}

        placeholders = ",".join("?" * len(memory_ids))
        cursor = self.conn.execute(
            f"""
            SELECT id, content, importance, memory_type, source, created_at, access_count
            FROM semantic_memory
            WHERE id IN ({placeholders})
            """,
            memory_ids,
        )

        results = []
        for row in cursor.fetchall():
            memory = Memory(
                id=row["id"],
                content=row["content"],
                importance=row["importance"],
                memory_type=row["memory_type"],
                source=row["source"],
                created_at=datetime.fromisoformat(row["created_at"]),
                access_count=row["access_count"],
            )
            # Convert distance to similarity (1 - distance for cosine)
            distance = distances[row["id"]]
            similarity = 1.0 - distance
            results.append(SearchResult(
                memory=memory,
                score=similarity,
                match_type="vector",
            ))

        # Sort by score (similarity) descending to preserve ranking
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def search_hybrid(
        self,
        query: str,
        embedding: Optional[list[float]] = None,
        limit: int = 10,
        vector_weight: float = 0.6,
    ) -> list[SearchResult]:
        """
        Hybrid search using RRF (Reciprocal Rank Fusion).

        Combines vector similarity (60%) and FTS (40%) by default.
        """
        fts_results = self.search_fts(query, limit=limit * 2)

        if embedding is not None and SQLITE_VEC_AVAILABLE:
            vec_results = self.search_vector(embedding, limit=limit * 2)
        else:
            vec_results = []

        # RRF fusion
        k = 60  # RRF constant
        scores: dict[int, float] = {}
        memories: dict[int, Memory] = {}

        # Score FTS results
        fts_weight = 1.0 - vector_weight
        for rank, result in enumerate(fts_results, start=1):
            memory_id = result.memory.id
            scores[memory_id] = scores.get(memory_id, 0) + fts_weight / (k + rank)
            memories[memory_id] = result.memory

        # Score vector results
        for rank, result in enumerate(vec_results, start=1):
            memory_id = result.memory.id
            scores[memory_id] = scores.get(memory_id, 0) + vector_weight / (k + rank)
            memories[memory_id] = result.memory

        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for memory_id in sorted_ids[:limit]:
            results.append(SearchResult(
                memory=memories[memory_id],
                score=scores[memory_id],
                match_type="hybrid",
            ))

        return results

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """Get a specific memory by ID."""
        cursor = self.conn.execute(
            """
            SELECT id, content, importance, memory_type, source, created_at, access_count
            FROM semantic_memory
            WHERE id = ?
            """,
            (memory_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        # Update access count
        self.conn.execute(
            "UPDATE semantic_memory SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
            (datetime.now().isoformat(), memory_id),
        )
        self.conn.commit()

        return Memory(
            id=row["id"],
            content=row["content"],
            importance=row["importance"],
            memory_type=row["memory_type"],
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
            access_count=row["access_count"] + 1,
        )

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        # Delete from vector table first
        if SQLITE_VEC_AVAILABLE:
            self.conn.execute("DELETE FROM vec_semantic WHERE memory_id = ?", (memory_id,))

        cursor = self.conn.execute(
            "DELETE FROM semantic_memory WHERE id = ?",
            (memory_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_recent_memories(self, limit: int = 5) -> list[Memory]:
        """
        Get most recent memories for LLM context injection.

        Args:
            limit: Maximum number of memories to return

        Returns:
            List of most recent memories, newest first
        """
        cursor = self.conn.execute(
            """
            SELECT id, content, importance, memory_type, source, created_at, access_count
            FROM semantic_memory
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(Memory(
                id=row["id"],
                content=row["content"],
                importance=row["importance"],
                memory_type=row["memory_type"],
                source=row["source"],
                created_at=datetime.fromisoformat(row["created_at"]),
                access_count=row["access_count"],
            ))
        return results

    def prune_old_memories(self, days: int = 90, min_importance: float = 0.3) -> int:
        """
        Remove memories older than X days AND importance < threshold.

        Args:
            days: Remove memories older than this many days
            min_importance: Only remove if importance is below this threshold

        Returns:
            Count of deleted memories
        """
        # First get IDs to delete (needed for vec_semantic cleanup)
        cursor = self.conn.execute(
            """
            SELECT id FROM semantic_memory
            WHERE created_at < datetime('now', ?)
            AND importance < ?
            """,
            (f"-{days} days", min_importance),
        )
        ids_to_delete = [row["id"] for row in cursor.fetchall()]

        if not ids_to_delete:
            return 0

        # Delete from vector table first
        if SQLITE_VEC_AVAILABLE:
            placeholders = ",".join("?" * len(ids_to_delete))
            self.conn.execute(
                f"DELETE FROM vec_semantic WHERE memory_id IN ({placeholders})",
                ids_to_delete,
            )

        # Delete from main table (FTS5 triggers handle fts_memory)
        placeholders = ",".join("?" * len(ids_to_delete))
        cursor = self.conn.execute(
            f"DELETE FROM semantic_memory WHERE id IN ({placeholders})",
            ids_to_delete,
        )
        self.conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for quick access
def get_store(db_path: str | Path | None = None) -> MemoryStore:
    """Get a memory store instance. Default: ~/.atlas/atlas.db"""
    return MemoryStore(db_path)
