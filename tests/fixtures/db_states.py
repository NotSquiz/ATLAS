"""
Database fixtures for UI testing.

Provides predefined player states for testing different UI scenarios
without manually earning XP.

Usage:
    # Load a fixture
    python -m tests.fixtures.db_states mid_level

    # Trigger a level-up
    python -m tests.fixtures.db_states level_up strength

    # In tests:
    from tests.fixtures.db_states import load_fixture, trigger_level_up
    load_fixture("new_player")

Available fixtures:
    - new_player: Fresh start, all skills Level 1
    - mid_level: Active player with mixed progress
    - about_to_level: 5 XP from level-up (animation testing)
    - max_level_veteran: Multiple 99s (endgame UI)
    - title_boundary: At title transition points
"""
import sqlite3
from pathlib import Path
from typing import Literal, Optional

# OSRS XP formula thresholds (approximate)
# Full formula in atlas/gamification/level_calculator.py
XP_FOR_LEVEL = {
    1: 0,
    5: 100,
    10: 1154,
    15: 2411,
    20: 5346,
    25: 8740,
    35: 22406,
    50: 101333,
    56: 166636,
    75: 1210421,
    76: 1336353,
    90: 5346332,
    91: 5902831,
    99: 13034431,
}


# Test fixtures with all 12 Lethal Gentleman skills
FIXTURES = {
    "new_player": {
        "description": "Fresh start - all skills Level 1",
        "skills": {
            # BODY (The Vessel)
            "strength": (1, 0),
            "endurance": (1, 0),
            "mobility": (1, 0),
            "nutrition": (1, 0),
            # MIND (The Citadel)
            "focus": (1, 0),
            "learning": (1, 0),
            "reflection": (1, 0),
            "creation": (1, 0),
            # SOUL (The Character)
            "presence": (1, 0),
            "service": (1, 0),
            "courage": (1, 0),
            "consistency": (1, 0),
        },
        "streak": 0,
        "today_xp": 0,
    },

    "mid_level": {
        "description": "Active player - mixed progress, 7-day streak",
        "skills": {
            # BODY - most active domain
            "strength": (25, 8740),
            "endurance": (18, 4470),
            "mobility": (22, 6517),
            "nutrition": (15, 2411),
            # MIND
            "focus": (20, 5346),
            "learning": (12, 1358),
            "reflection": (8, 512),
            "creation": (16, 2863),
            # SOUL
            "presence": (10, 1000),
            "service": (5, 100),
            "courage": (14, 2107),
            "consistency": (19, 4824),
        },
        "streak": 7,
        "today_xp": 450,
    },

    "about_to_level": {
        "description": "5 XP from level-up in Strength (animation testing)",
        "skills": {
            "strength": (24, 8735),  # Level 25 at 8740 XP
            "endurance": (15, 2411),
            "mobility": (18, 4470),
            "nutrition": (10, 1000),
            "focus": (12, 1358),
            "learning": (8, 512),
            "reflection": (5, 100),
            "creation": (10, 1000),
            "presence": (7, 363),
            "service": (3, 40),
            "courage": (9, 760),
            "consistency": (14, 2107),
        },
        "streak": 5,
        "today_xp": 200,
    },

    "max_level_veteran": {
        "description": "Endgame player - multiple 99s, max streak",
        "skills": {
            "strength": (99, 13034431),
            "endurance": (99, 13034431),
            "mobility": (75, 1210421),
            "nutrition": (60, 273742),
            "focus": (99, 13034431),
            "learning": (50, 101333),
            "reflection": (45, 61512),
            "creation": (80, 1986068),
            "presence": (55, 166636),
            "service": (40, 37224),
            "courage": (65, 449428),
            "consistency": (99, 13034431),
        },
        "streak": 14,
        "today_xp": 1200,
    },

    "title_boundary": {
        "description": "At Octalysis title transition boundaries",
        "skills": {
            # Each at a title boundary (titles change at 16, 36, 56, 76, 91)
            "strength": (15, 2411),     # About to become Practitioner (16)
            "endurance": (35, 22406),   # About to become Journeyman (36)
            "mobility": (55, 166636),   # About to become Adept (56)
            "nutrition": (10, 1000),
            "focus": (75, 1210421),     # About to become Master (76)
            "learning": (25, 8740),
            "reflection": (12, 1358),
            "creation": (90, 5346332),  # About to become Grandmaster (91)
            "presence": (20, 5346),
            "service": (8, 512),
            "courage": (5, 100),
            "consistency": (30, 13363),
        },
        "streak": 10,
        "today_xp": 800,
    },

    "domain_focus_body": {
        "description": "Body domain focused player",
        "skills": {
            # BODY - high levels
            "strength": (50, 101333),
            "endurance": (45, 61512),
            "mobility": (40, 37224),
            "nutrition": (35, 22406),
            # MIND - low levels
            "focus": (10, 1000),
            "learning": (8, 512),
            "reflection": (5, 100),
            "creation": (7, 363),
            # SOUL - medium levels
            "presence": (15, 2411),
            "service": (12, 1358),
            "courage": (18, 4470),
            "consistency": (25, 8740),
        },
        "streak": 14,
        "today_xp": 600,
    },
}

# Type alias for fixture names
FixtureName = Literal[
    "new_player",
    "mid_level",
    "about_to_level",
    "max_level_veteran",
    "title_boundary",
    "domain_focus_body",
]


def load_fixture(
    fixture_name: FixtureName,
    db_path: Optional[str] = None,
) -> str:
    """
    Load a test fixture into the database.

    WARNING: This REPLACES existing skill data. Use only for testing.

    Args:
        fixture_name: One of the predefined fixtures
        db_path: Database path (defaults to ~/.atlas/atlas.db)

    Returns:
        Description of loaded fixture

    Raises:
        ValueError: If fixture_name is unknown
    """
    if db_path is None:
        db_path = str(Path.home() / ".atlas" / "atlas.db")

    fixture = FIXTURES.get(fixture_name)
    if not fixture:
        available = list(FIXTURES.keys())
        raise ValueError(f"Unknown fixture: {fixture_name}. Available: {available}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Update skills (preserving domain/virtue metadata from schema)
        for skill_name, (level, xp) in fixture["skills"].items():
            cursor.execute("""
                UPDATE player_skills
                SET current_xp = ?, current_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE skill_name = ?
            """, (xp, level, skill_name))

        # Clear XP events and add today's XP if specified
        cursor.execute("DELETE FROM xp_events")
        if fixture["today_xp"] > 0:
            # Distribute today's XP across a few skills for realism
            xp_per_event = fixture["today_xp"] // 3
            for skill in ["strength", "mobility", "consistency"]:
                cursor.execute("""
                    INSERT INTO xp_events (skill_name, xp_gained, source_type, created_at)
                    VALUES (?, ?, 'fixture_load', CURRENT_TIMESTAMP)
                """, (skill, xp_per_event))

        # Set streak
        cursor.execute("DELETE FROM activity_streaks")
        if fixture["streak"] > 0:
            cursor.execute("""
                INSERT INTO activity_streaks (date, streak_day, activities_logged)
                VALUES (DATE('now'), ?, 1)
            """, (fixture["streak"],))

        conn.commit()
        return f"Loaded fixture: {fixture_name} - {fixture['description']}"

    finally:
        conn.close()


def trigger_level_up(
    skill: str = "strength",
    db_path: Optional[str] = None,
) -> str:
    """
    Award enough XP to trigger a level-up.

    Used for testing level-up animations and sounds.

    Args:
        skill: Skill to level up
        db_path: Database path (defaults to ~/.atlas/atlas.db)

    Returns:
        Description of XP awarded and new level
    """
    if db_path is None:
        db_path = str(Path.home() / ".atlas" / "atlas.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get current XP and level
        cursor.execute(
            "SELECT current_xp, current_level FROM player_skills WHERE skill_name = ?",
            (skill,)
        )
        row = cursor.fetchone()
        if not row:
            return f"Skill not found: {skill}"

        current_xp, current_level = row

        # Check max level
        next_level = current_level + 1
        if next_level > 99:
            return f"{skill} is already at max level (99)"

        # Calculate XP threshold for next level using OSRS formula
        next_threshold = int(sum(
            int(i + 300 * (2 ** (i / 7))) / 4
            for i in range(1, next_level + 1)
        ))

        xp_needed = max(1, next_threshold - current_xp + 1)

        # Award XP
        cursor.execute("""
            UPDATE player_skills
            SET current_xp = current_xp + ?, current_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE skill_name = ?
        """, (xp_needed, next_level, skill))

        cursor.execute("""
            INSERT INTO xp_events (skill_name, xp_gained, source_type)
            VALUES (?, ?, 'test_level_up')
        """, (skill, xp_needed))

        conn.commit()
        return f"Awarded {xp_needed} XP to {skill}, now level {next_level}"

    finally:
        conn.close()


def get_fixture_summary() -> str:
    """Get a summary of all available fixtures."""
    lines = ["Available fixtures:", ""]
    for name, data in FIXTURES.items():
        total_level = sum(lvl for lvl, _ in data["skills"].values())
        total_xp = sum(xp for _, xp in data["skills"].values())
        lines.append(f"  {name:20} - Level {total_level:4}, {total_xp:,} XP - {data['description']}")
    return "\n".join(lines)


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tests.fixtures.db_states <fixture_name>")
        print("       python -m tests.fixtures.db_states level_up [skill]")
        print()
        print(get_fixture_summary())
        sys.exit(0)

    command = sys.argv[1]

    if command == "level_up":
        skill = sys.argv[2] if len(sys.argv) > 2 else "strength"
        result = trigger_level_up(skill)
        print(result)

    elif command == "list":
        print(get_fixture_summary())

    elif command in FIXTURES:
        result = load_fixture(command)
        print(result)

    else:
        print(f"Unknown command/fixture: {command}")
        print()
        print(get_fixture_summary())
        sys.exit(1)
