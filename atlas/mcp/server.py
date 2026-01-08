"""
ATLAS MCP Server

FastMCP-based unified server with STDIO transport.
Provides tools for memory operations and daily logging.
"""

from datetime import date
from pathlib import Path
from typing import Optional

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None

from atlas.memory.store import MemoryStore, get_store


# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "atlas.db"


def create_server(db_path: Optional[Path] = None) -> "FastMCP":
    """Create and configure the MCP server."""
    if not FASTMCP_AVAILABLE:
        raise ImportError(
            "FastMCP not installed. Run: pip install fastmcp"
        )

    mcp = FastMCP("ATLAS")
    store = get_store(db_path or DEFAULT_DB_PATH)

    # Ensure database is initialized
    store.init_db()

    # ==========================================
    # MEMORY TOOLS
    # ==========================================

    @mcp.tool()
    def memory_store(
        content: str,
        importance: float = 0.5,
        memory_type: str = "general",
        source: str = "user",
    ) -> dict:
        """
        Store a memory in ATLAS's long-term memory.

        Args:
            content: The memory content to store
            importance: Importance score from 0.0 to 1.0 (default 0.5)
            memory_type: Type of memory - 'general', 'fact', 'preference', or 'event'
            source: Where this memory came from (default 'user')

        Returns:
            Dictionary with the stored memory ID
        """
        memory_id = store.add_memory(
            content=content,
            importance=importance,
            memory_type=memory_type,
            source=source,
        )
        return {
            "status": "stored",
            "memory_id": memory_id,
            "content": content[:100] + "..." if len(content) > 100 else content,
        }

    @mcp.tool()
    def memory_search(
        query: str,
        limit: int = 5,
    ) -> dict:
        """
        Search ATLAS's memories using full-text search.

        Args:
            query: Search query
            limit: Maximum number of results (default 5)

        Returns:
            Dictionary with matching memories
        """
        results = store.search_fts(query, limit=limit)
        return {
            "query": query,
            "count": len(results),
            "memories": [
                {
                    "id": r.memory.id,
                    "content": r.memory.content,
                    "importance": r.memory.importance,
                    "type": r.memory.memory_type,
                    "score": r.score,
                }
                for r in results
            ],
        }

    @mcp.tool()
    def memory_get(memory_id: int) -> dict:
        """
        Retrieve a specific memory by ID.

        Args:
            memory_id: The ID of the memory to retrieve

        Returns:
            The memory content and metadata
        """
        memory = store.get_memory(memory_id)
        if memory is None:
            return {"error": f"Memory {memory_id} not found"}
        return {
            "id": memory.id,
            "content": memory.content,
            "importance": memory.importance,
            "type": memory.memory_type,
            "source": memory.source,
            "created_at": memory.created_at.isoformat(),
            "access_count": memory.access_count,
        }

    @mcp.tool()
    def memory_delete(memory_id: int) -> dict:
        """
        Delete a memory by ID.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            Status of the deletion
        """
        success = store.delete_memory(memory_id)
        if success:
            return {"status": "deleted", "memory_id": memory_id}
        return {"error": f"Memory {memory_id} not found"}

    # ==========================================
    # DAILY LOGGING TOOLS
    # ==========================================

    @mcp.tool()
    def daily_log(
        energy_level: Optional[int] = None,
        mood: Optional[int] = None,
        stress_level: Optional[int] = None,
        sleep_hours: Optional[float] = None,
        weight_kg: Optional[float] = None,
        notes: Optional[str] = None,
        log_date: Optional[str] = None,
    ) -> dict:
        """
        Log daily metrics for Blueprint tracking.

        Args:
            energy_level: Energy level 1-10
            mood: Mood level 1-10
            stress_level: Stress level 1-10
            sleep_hours: Hours of sleep
            weight_kg: Weight in kilograms
            notes: Additional notes
            log_date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            Status of the log entry
        """
        target_date = log_date or date.today().isoformat()

        # Build update fields
        fields = []
        values = []

        if energy_level is not None:
            fields.append("energy_level = ?")
            values.append(energy_level)
        if mood is not None:
            fields.append("mood = ?")
            values.append(mood)
        if stress_level is not None:
            fields.append("stress_level = ?")
            values.append(stress_level)
        if sleep_hours is not None:
            fields.append("sleep_hours = ?")
            values.append(sleep_hours)
        if weight_kg is not None:
            fields.append("weight_kg = ?")
            values.append(weight_kg)
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes)

        if not fields:
            return {"error": "No metrics provided"}

        # Upsert daily metrics
        conn = store.conn
        cursor = conn.execute(
            "SELECT id FROM daily_metrics WHERE date = ?",
            (target_date,),
        )
        row = cursor.fetchone()

        if row:
            # Update existing
            fields.append("updated_at = CURRENT_TIMESTAMP")
            sql = f"UPDATE daily_metrics SET {', '.join(fields)} WHERE date = ?"
            values.append(target_date)
            conn.execute(sql, values)
        else:
            # Insert new
            insert_fields = ["date"] + [f.split(" = ")[0] for f in fields if "updated_at" not in f]
            insert_values = [target_date] + values
            placeholders = ", ".join(["?"] * len(insert_values))
            sql = f"INSERT INTO daily_metrics ({', '.join(insert_fields)}) VALUES ({placeholders})"
            conn.execute(sql, insert_values)

        conn.commit()

        return {
            "status": "logged",
            "date": target_date,
            "metrics_updated": len(fields),
        }

    @mcp.tool()
    def supplement_log(
        supplement_name: str,
        taken: bool = True,
        time: Optional[str] = None,
        notes: Optional[str] = None,
        log_date: Optional[str] = None,
    ) -> dict:
        """
        Log that a supplement was taken.

        Args:
            supplement_name: Name of the supplement
            taken: Whether it was taken (default True)
            time: Time taken in HH:MM format
            notes: Additional notes
            log_date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            Status of the log entry
        """
        target_date = log_date or date.today().isoformat()
        conn = store.conn

        # Find or create supplement
        cursor = conn.execute(
            "SELECT id FROM supplements WHERE name = ?",
            (supplement_name,),
        )
        row = cursor.fetchone()

        if row:
            supplement_id = row["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO supplements (name) VALUES (?)",
                (supplement_name,),
            )
            supplement_id = cursor.lastrowid

        # Log the supplement
        conn.execute(
            """
            INSERT INTO supplement_log (supplement_id, date, time, taken, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (supplement_id, target_date, time, taken, notes),
        )
        conn.commit()

        return {
            "status": "logged",
            "supplement": supplement_name,
            "date": target_date,
            "taken": taken,
        }

    # ==========================================
    # WORKOUT TOOLS
    # ==========================================

    @mcp.tool()
    def workout_log(
        workout_type: str,
        duration_minutes: int,
        exercises: Optional[list[dict]] = None,
        energy_before: Optional[int] = None,
        energy_after: Optional[int] = None,
        notes: Optional[str] = None,
        workout_date: Optional[str] = None,
    ) -> dict:
        """
        Log a completed workout.

        Args:
            workout_type: Type of workout - 'strength', 'cardio', 'mobility', 'rehab'
            duration_minutes: Duration in minutes
            exercises: List of exercises, each with:
                - exercise_id: Exercise identifier
                - exercise_name: Exercise name
                - sets: Number of sets (for strength)
                - reps: Reps per set as string "8,8,6"
                - weight_kg: Weight used
                - duration_seconds: Duration (for cardio)
                - distance_meters: Distance (for cardio)
            energy_before: Energy level before workout (1-10)
            energy_after: Energy level after workout (1-10)
            notes: Additional notes
            workout_date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            Status with workout ID
        """
        target_date = workout_date or date.today().isoformat()
        conn = store.conn

        # Insert workout
        cursor = conn.execute(
            """
            INSERT INTO workouts (date, type, duration_minutes, energy_before, energy_after, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (target_date, workout_type, duration_minutes, energy_before, energy_after, notes),
        )
        workout_id = cursor.lastrowid

        # Insert exercises if provided
        exercise_count = 0
        if exercises:
            for idx, ex in enumerate(exercises):
                conn.execute(
                    """
                    INSERT INTO workout_exercises
                    (workout_id, exercise_id, exercise_name, sets, reps, weight_kg,
                     duration_seconds, distance_meters, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workout_id,
                        ex.get("exercise_id", ""),
                        ex.get("exercise_name", ""),
                        ex.get("sets"),
                        ex.get("reps"),
                        ex.get("weight_kg"),
                        ex.get("duration_seconds"),
                        ex.get("distance_meters"),
                        idx,
                    ),
                )
                exercise_count += 1

        conn.commit()

        return {
            "status": "logged",
            "workout_id": workout_id,
            "date": target_date,
            "type": workout_type,
            "duration_minutes": duration_minutes,
            "exercises_logged": exercise_count,
        }

    # ==========================================
    # INJURY TOOLS
    # ==========================================

    @mcp.tool()
    def injury_update(
        body_part: str,
        severity: Optional[int] = None,
        status: Optional[str] = None,
        side: Optional[str] = None,
        description: Optional[str] = None,
        contraindicated_exercises: Optional[list[str]] = None,
        rehab_notes: Optional[str] = None,
    ) -> dict:
        """
        Update or create an injury record.

        Args:
            body_part: Body part affected (e.g., 'shoulder', 'lower_back', 'knee')
            severity: Severity level 1-5 (1=minor, 5=severe)
            status: Status - 'active', 'recovering', 'resolved'
            side: Side affected - 'left', 'right', 'both', 'n/a'
            description: Description of the injury
            contraindicated_exercises: List of exercise IDs to avoid
            rehab_notes: Notes on rehabilitation

        Returns:
            Status with injury ID
        """
        import json

        conn = store.conn

        # Check for existing injury
        cursor = conn.execute(
            """
            SELECT id, severity, status, contraindicated_exercises, rehab_notes
            FROM injuries
            WHERE body_part = ? AND (side = ? OR side IS NULL)
            AND status != 'resolved'
            """,
            (body_part, side),
        )
        row = cursor.fetchone()

        if row:
            # Update existing injury
            injury_id = row["id"]
            updates = []
            values = []

            if severity is not None:
                updates.append("severity = ?")
                values.append(severity)
            if status is not None:
                updates.append("status = ?")
                values.append(status)
            if description is not None:
                updates.append("description = ?")
                values.append(description)
            if contraindicated_exercises is not None:
                updates.append("contraindicated_exercises = ?")
                values.append(json.dumps(contraindicated_exercises))
            if rehab_notes is not None:
                updates.append("rehab_notes = ?")
                values.append(rehab_notes)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                sql = f"UPDATE injuries SET {', '.join(updates)} WHERE id = ?"
                values.append(injury_id)
                conn.execute(sql, values)
                conn.commit()

            return {
                "status": "updated",
                "injury_id": injury_id,
                "body_part": body_part,
            }
        else:
            # Create new injury
            cursor = conn.execute(
                """
                INSERT INTO injuries
                (body_part, side, severity, status, description, contraindicated_exercises, rehab_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    body_part,
                    side or "n/a",
                    severity or 3,
                    status or "active",
                    description,
                    json.dumps(contraindicated_exercises) if contraindicated_exercises else None,
                    rehab_notes,
                ),
            )
            injury_id = cursor.lastrowid
            conn.commit()

            return {
                "status": "created",
                "injury_id": injury_id,
                "body_part": body_part,
                "severity": severity or 3,
            }

    @mcp.tool()
    def injury_list(status: Optional[str] = None) -> dict:
        """
        List all injuries, optionally filtered by status.

        Args:
            status: Filter by status - 'active', 'recovering', 'resolved'

        Returns:
            List of injuries
        """
        import json

        conn = store.conn

        if status:
            cursor = conn.execute(
                "SELECT * FROM injuries WHERE status = ? ORDER BY severity DESC",
                (status,),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM injuries WHERE status != 'resolved' ORDER BY severity DESC"
            )

        injuries = []
        for row in cursor.fetchall():
            contraindicated = row["contraindicated_exercises"]
            injuries.append({
                "id": row["id"],
                "body_part": row["body_part"],
                "side": row["side"],
                "severity": row["severity"],
                "status": row["status"],
                "description": row["description"],
                "contraindicated_exercises": json.loads(contraindicated) if contraindicated else [],
            })

        return {
            "count": len(injuries),
            "injuries": injuries,
        }

    return mcp


# Server instance for CLI
_server: Optional["FastMCP"] = None


def get_server() -> "FastMCP":
    """Get or create the server instance."""
    global _server
    if _server is None:
        _server = create_server()
    return _server


def main():
    """Run the MCP server."""
    if not FASTMCP_AVAILABLE:
        print("Error: FastMCP not installed. Run: pip install fastmcp")
        return 1

    server = get_server()
    server.run()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
