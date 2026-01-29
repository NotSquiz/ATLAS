"""
ATLAS XP Service

Handles XP awards, skill tracking, and level calculations.

Design decisions (from verification review):
- Non-blocking: award_xp_async() for voice pipeline (fire-and-forget)
- Fail-safe: XP failures never break core health tracking
- Atomic: Uses transactions for xp_events + player_skills updates
- Validated: Skill names normalized, XP values bounded
- Reconcilable: Can verify SUM(xp_events) == player_skills.current_xp

XP Economy (calibrated for ~1 year to Level 50):
- Daily activities: 200-400 XP/day typical
- Level 10: ~1,154 XP (3-6 days)
- Level 25: ~8,740 XP (3-4 weeks)
- Level 50: ~101,333 XP (8-12 months)
- Level 99: ~13M XP (aspirational, multi-year)

Usage:
    from atlas.gamification import get_xp_service

    service = get_xp_service()

    # Async award (non-blocking, for voice pipeline)
    leveled_up = service.award_xp_async("strength", 100, "workout_strength")
    if leveled_up:
        # Announce level-up via voice

    # Sync award (blocking, for CLI/testing)
    result = service.award_xp("mobility", 50, "morning_routine")
"""

import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Tuple, Callable

from atlas.gamification.level_calculator import (
    level_for_xp,
    xp_for_level,
    xp_to_next_level,
    progress_to_next_level,
    calculate_combat_level_from_total,
    skills_to_next_combat_level,
    MAX_LEVEL,
    COMBAT_LEVEL_MAX,
)

logger = logging.getLogger(__name__)


class SkillDomain(Enum):
    """The three domains of the Lethal Gentleman Framework."""
    BODY = "body"    # The Vessel
    MIND = "mind"    # The Citadel
    SOUL = "soul"    # The Character


class SkillName(Enum):
    """
    Valid skill names (12-skill Lethal Gentleman Framework).

    BODY (4): Strength, Endurance, Mobility, Nutrition
    MIND (4): Focus, Learning, Reflection, Creation
    SOUL (4): Presence, Service, Courage, Consistency
    """
    # BODY - The Vessel
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    MOBILITY = "mobility"
    NUTRITION = "nutrition"
    # MIND - The Citadel
    FOCUS = "focus"
    LEARNING = "learning"
    REFLECTION = "reflection"
    CREATION = "creation"
    # SOUL - The Character
    PRESENCE = "presence"
    SERVICE = "service"
    COURAGE = "courage"
    CONSISTENCY = "consistency"


# Skill metadata (domain, virtue, shadow warning)
SKILL_METADATA = {
    # BODY
    "strength": ("body", "Power", "Brutality without control"),
    "endurance": ("body", "Grit", "Self-destruction"),
    "mobility": ("body", "Readiness", "Preparation as procrastination"),
    "nutrition": ("body", "Temperance", "Orthorexia"),
    # MIND
    "focus": ("mind", "Clarity", "Obsession without perspective"),
    "learning": ("mind", "Wisdom", "Intellectual vanity"),
    "reflection": ("mind", "Self-Knowledge", "Rumination without action"),
    "creation": ("mind", "Courage Made Manifest", "Ego expression without purpose"),
    # SOUL
    "presence": ("soul", "Justice to Others", "Enmeshment, boundary loss"),
    "service": ("soul", "Generativity", "Martyrdom, self-neglect"),
    "courage": ("soul", "Facing Fear", "Recklessness"),
    "consistency": ("soul", "Discipline", "Rigidity, streak obsession"),
}


# XP award values (calibrated for realistic progression)
# Target: Level 50 achievable in 8-12 months of consistent daily activity
# 12-Skill Lethal Gentleman Framework
XP_TABLE = {
    # ============================================
    # BODY SKILLS (The Vessel)
    # ============================================

    # Strength: Power through weight training
    "workout_strength": 150,       # Strength A/B/C session
    "heavy_lift": 50,              # PR or heavy single
    "grip_work": 25,               # Dedicated grip training

    # Endurance: Grit through sustained effort
    "workout_cardio": 120,         # Zone 2, cardio activities
    "cold_exposure": 40,           # Cold shower, ice bath
    "ruck": 80,                    # Weighted ruck/walk
    "rest_day": 50,                # Taking a scheduled rest day (recovery = endurance)

    # Mobility: Readiness through movement practice
    "morning_routine": 75,         # 18-min routine completion
    "mobility_exercise": 20,       # Individual mobility work
    "stretch_session": 40,         # Dedicated flexibility work

    # Nutrition: Temperance through mindful eating
    "supplement_batch": 25,        # Per timing batch (preworkout/breakfast/bedtime)
    "meal_log": 40,                # Per meal logged
    "protein_target": 30,          # Hit daily protein goal
    "fast_complete": 50,           # Completed intentional fast

    # ============================================
    # MIND SKILLS (The Citadel)
    # ============================================

    # Focus: Clarity through deep work
    "deep_work_block": 100,        # 90+ minute focused session
    "pomodoro_complete": 25,       # 25-min focused block
    "device_detox": 40,            # Phone-free period (2+ hours)

    # Learning: Wisdom through study
    "book_chapter": 35,            # Chapter completed
    "course_lesson": 50,           # Course/tutorial lesson
    "skill_practice": 45,          # Deliberate practice session
    "question_documented": 15,     # Captured question to explore

    # Reflection: Self-knowledge through inquiry
    "evening_audit": 60,           # Seneca's Trial completed
    "journal_entry": 35,           # Written reflection
    "memento_mori": 25,            # Death meditation complete
    "premeditatio": 30,            # Premeditatio Malorum (negative visualization)

    # Creation: Courage made manifest through shipping
    "project_shipped": 200,        # Work completed and delivered
    "content_published": 100,      # Article, video, etc.
    "work_session": 75,            # "logged work" voice command
    "work_capture": 30,            # ThoughtClassifier -> baby-brains

    # ============================================
    # SOUL SKILLS (The Character)
    # ============================================

    # Presence: Justice to others through attention
    "device_free_family": 50,      # 30+ min with family, no devices
    "undivided_attention": 30,     # Quality conversation logged
    "active_listening": 25,        # Focused listening session

    # Service: Generativity through giving
    "mentoring_session": 75,       # Teaching/mentoring others
    "community_contribution": 50,  # Helping beyond family
    "teaching_moment": 30,         # Shared knowledge with someone

    # Courage: Facing fear through action
    "hard_conversation": 75,       # Difficult truth spoken
    "fear_faced": 100,             # Deliberate discomfort embraced
    "boundary_set": 50,            # Said no when needed
    "vulnerability_shared": 40,    # Authentic self-disclosure

    # Consistency: Discipline through showing up
    "daily_checkin": 30,           # First activity of day
    "streak_bonus": 5,             # Per consecutive day (capped)
    "commitment_kept": 40,         # Followed through on promise

    # Octalysis: Strategic Rest (counter to Consistency shadow)
    # From research: "Celebrate strategic rest rather than just persistence"
    "strategic_rest_planned": 50,  # Planned recovery day taken
    "strategic_rest_recovery": 40, # Rest due to body signals
    "strategic_rest_life": 30,     # Life circumstances (grace period used)
    "flexibility_bonus": 25,       # Awarded when streak freeze used wisely

    # ============================================
    # SPECIAL EVENTS (Cross-skill)
    # ============================================
    "assessment_complete": 250,    # Baseline assessment session
    "weight_log": 20,              # Body composition logging
    "gate_passed": 500,            # GATE 1/2/3/4 milestone

    # Failure Codex (processing setbacks = growth)
    "failure_tier1": 25,           # Bad day processed well
    "failure_tier2": 50,           # Missed target analyzed
    "failure_tier3": 100,          # Major setback → growth documented

    # Garmin integration
    "sleep_good": 60,              # Garmin sleep score >= 80
    "body_battery_good": 30,       # Body battery >= 50 at morning sync
}

# Streak bonus caps at 14 days (70 XP max from streaks per action)
MAX_STREAK_DAYS = 14

# XP cap per skill (slightly above Level 99 requirement)
MAX_XP_PER_SKILL = 15_000_000


# ==============================================================================
# OCTALYSIS-INFORMED TITLE SYSTEM
# From research: "Titles should reflect transformation, not just numerical progress"
# ==============================================================================

SKILL_TITLES = {
    # Level ranges map to titles reflecting growth journey
    # Based on Octalysis Core Drive 1 (Epic Meaning & Calling)
    (1, 15): ("Apprentice", "Learning the foundations"),
    (16, 35): ("Practitioner", "Building consistent practice"),
    (36, 55): ("Journeyman", "Developing true competence"),
    (56, 75): ("Adept", "Mastering the craft"),
    (76, 90): ("Master", "Teaching others"),
    (91, 99): ("Grandmaster", "Living embodiment"),
}


def get_title_for_level(level: int) -> tuple[str, str]:
    """Get title and description for a skill level."""
    for (min_lvl, max_lvl), (title, desc) in SKILL_TITLES.items():
        if min_lvl <= level <= max_lvl:
            return title, desc
    return "Grandmaster", "Living embodiment"


# ==============================================================================
# OCTALYSIS-INFORMED STREAK MECHANICS
# From research: "Streaks require forgiveness to remain ethical"
# Key principles:
# - Rolling windows (5 of 7 days) prevent catastrophic loss
# - Streak freezes provide "safety nets"
# - Strategic rest is celebrated, not penalized
# ==============================================================================

# Rolling window: 5 of last 7 days counts as "consistent"
ROLLING_WINDOW_DAYS = 7
ROLLING_WINDOW_THRESHOLD = 5

# Streak freezes: Users earn 1 freeze per 7 consecutive days (max 3 stored)
MAX_STREAK_FREEZES = 3

# Grace period: 1 day grace for missed activity before streak breaks
GRACE_PERIOD_DAYS = 1


# ==============================================================================
# SKILL-TO-CORE-DRIVE MAPPING (Octalysis Framework)
# From research: Primary drives that power each skill
# CD1=Epic Meaning, CD2=Accomplishment, CD3=Creativity,
# CD4=Ownership, CD5=Social, CD6=Scarcity, CD7=Unpredictability, CD8=Loss Avoidance
# ==============================================================================

SKILL_DRIVES = {
    # BODY - Primary: CD2 (Accomplishment), CD4 (Ownership of body)
    "strength": ("CD2", "CD4", "Progress tracking, PR records, body investment"),
    "endurance": ("CD1", "CD7", "Epic journey narrative, unpredictable routes"),
    "mobility": ("CD3", "CD2", "Movement exploration, unlockable progressions"),
    "nutrition": ("CD4", "CD8", "Food ownership, health loss avoidance (careful)"),

    # MIND - Primary: CD3 (Creativity), CD1 (Epic Meaning)
    "focus": ("CD6", "CD3", "Time-boxing scarcity, choosing focus methods"),
    "learning": ("CD3", "CD7", "Mastery path choices, unlock discoveries"),
    "reflection": ("CD1", "CD4", "Wisdom contribution, journal ownership"),
    "creation": ("CD3", "CD5", "Creative expression, sharing and feedback"),

    # SOUL - Primary: CD1 (Epic Meaning), CD5 (Social Influence)
    "presence": ("CD3", "CD7", "Moment awareness as practice, state curiosity"),
    "service": ("CD1", "CD5", "Higher purpose, community impact"),
    "courage": ("CD8", "CD2", "Regret avoidance, fear-facing achievements"),
    "consistency": ("CD2", "CD3", "Streak accomplishment + FLEXIBILITY counter"),
}


@dataclass
class Skill:
    """Represents a player skill with XP, level, and metadata."""
    name: str
    xp: int
    level: int
    domain: str = "body"
    virtue: str = ""
    shadow_warning: str = ""

    @property
    def xp_to_next(self) -> int:
        """XP remaining to reach next level."""
        return xp_to_next_level(self.xp)

    @property
    def progress_pct(self) -> float:
        """Progress percentage toward next level."""
        _, _, pct = progress_to_next_level(self.xp)
        return pct

    @property
    def title(self) -> str:
        """Get Octalysis-informed title for current level."""
        title, _ = get_title_for_level(self.level)
        return title

    @property
    def title_description(self) -> str:
        """Get description for current title tier."""
        _, desc = get_title_for_level(self.level)
        return desc

    @property
    def drives(self) -> tuple[str, str, str]:
        """Get Core Drive mapping for this skill."""
        return SKILL_DRIVES.get(self.name, ("CD2", "CD3", "Default drives"))

    def to_voice(self) -> str:
        """Format for voice announcement."""
        return f"{self.name.title()} level {self.level}"

    def to_voice_with_title(self) -> str:
        """Format for voice with Octalysis title."""
        return f"{self.name.title()} level {self.level}, {self.title}"

    @classmethod
    def from_metadata(cls, name: str, xp: int, level: int) -> "Skill":
        """Create skill with metadata from SKILL_METADATA."""
        domain, virtue, shadow = SKILL_METADATA.get(
            name, ("body", "", "")
        )
        return cls(
            name=name,
            xp=xp,
            level=level,
            domain=domain,
            virtue=virtue,
            shadow_warning=shadow
        )


@dataclass
class XPAwardResult:
    """Result of an XP award operation."""
    skill_name: str
    xp_awarded: int
    new_total_xp: int
    old_level: int
    new_level: int
    leveled_up: bool
    source: str

    @property
    def new_title(self) -> str:
        """Get Octalysis title for new level."""
        title, _ = get_title_for_level(self.new_level)
        return title

    @property
    def title_changed(self) -> bool:
        """Check if title tier changed (more significant than level-up)."""
        old_title, _ = get_title_for_level(self.old_level)
        new_title, _ = get_title_for_level(self.new_level)
        return old_title != new_title

    def level_up_message(self) -> Optional[str]:
        """Get level-up announcement text."""
        if not self.leveled_up:
            return None
        return f"Level up! {self.skill_name.title()} is now {self.new_level}."

    def level_up_message_with_title(self) -> Optional[str]:
        """
        Get level-up announcement with Octalysis title.

        From research: "Titles should reflect transformation, not just numbers."
        Title changes are celebrated more than regular level-ups.
        """
        if not self.leveled_up:
            return None

        base = f"Level up! {self.skill_name.title()} is now {self.new_level}"

        if self.title_changed:
            # Major milestone - title transition
            new_title, desc = get_title_for_level(self.new_level)
            return f"{base}. You've become a {new_title}. {desc}."
        else:
            return f"{base}."


class XPService:
    """
    Service for awarding XP and tracking skill levels.

    Thread-safe with connection-per-thread pattern.
    Uses transactions for atomic updates.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "atlas.db"
        self._local = threading.local()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="xp_")
        self._level_up_callback: Optional[Callable[[XPAwardResult], None]] = None
        self._ensure_tables()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, timeout=10.0)
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.conn.execute("PRAGMA journal_mode = WAL")
        return self._local.conn

    def _ensure_tables(self):
        """Create gamification tables if they don't exist."""
        conn = self._get_conn()
        try:
            # First, check if we need to migrate from old schema
            cursor = conn.execute("PRAGMA table_info(player_skills)")
            columns = {row[1] for row in cursor.fetchall()}

            if "domain" not in columns and "skill_name" in columns:
                # Old schema - need to migrate
                logger.info("Migrating player_skills to 12-skill schema")
                self._migrate_to_12_skills(conn)
            else:
                # Create fresh tables
                self._create_fresh_tables(conn)

            conn.commit()
            logger.debug("Gamification tables initialized")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize gamification tables: {e}")
            raise

    def _create_fresh_tables(self, conn: sqlite3.Connection):
        """Create fresh gamification tables with 12-skill schema."""
        conn.executescript("""
            -- Player skill levels (12-skill framework)
            CREATE TABLE IF NOT EXISTS player_skills (
                skill_name TEXT PRIMARY KEY,
                domain TEXT NOT NULL DEFAULT 'body' CHECK(domain IN ('body', 'mind', 'soul')),
                virtue TEXT NOT NULL DEFAULT '',
                shadow_warning TEXT,
                current_xp INTEGER DEFAULT 0 CHECK(current_xp >= 0 AND current_xp <= 15000000),
                current_level INTEGER DEFAULT 1 CHECK(current_level >= 1 AND current_level <= 99),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- XP event log (audit trail)
            CREATE TABLE IF NOT EXISTS xp_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                xp_gained INTEGER NOT NULL CHECK(xp_gained > 0),
                source_type TEXT NOT NULL,
                streak_bonus INTEGER DEFAULT 0,
                failure_tier INTEGER CHECK(failure_tier IS NULL OR failure_tier IN (1, 2, 3)),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (skill_name) REFERENCES player_skills(skill_name)
            );

            -- Activity streaks (for bonus calculation)
            CREATE TABLE IF NOT EXISTS activity_streaks (
                date DATE PRIMARY KEY,
                streak_day INTEGER NOT NULL CHECK(streak_day >= 1),
                activities_logged INTEGER DEFAULT 1
            );

            -- Daily reflections (Seneca's Trial)
            CREATE TABLE IF NOT EXISTS daily_reflections (
                date DATE PRIMARY KEY,
                prosecution TEXT,
                judgment TEXT,
                advocacy TEXT,
                virtue_focus TEXT,
                virtue_score INTEGER CHECK(virtue_score IS NULL OR (virtue_score >= 1 AND virtue_score <= 10)),
                memento_mori_complete BOOLEAN DEFAULT FALSE,
                xp_awarded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_xp_events_skill ON xp_events(skill_name);
            CREATE INDEX IF NOT EXISTS idx_xp_events_date ON xp_events(created_at);
            CREATE INDEX IF NOT EXISTS idx_xp_events_source ON xp_events(source_type);

            -- Octalysis-informed streak forgiveness system
            -- From research: "Streaks require forgiveness to remain ethical"
            CREATE TABLE IF NOT EXISTS streak_freezes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                earned_at DATE NOT NULL,
                used_at DATE,
                expired BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Strategic rest tracking (counter to Consistency shadow)
            CREATE TABLE IF NOT EXISTS strategic_rest (
                date DATE PRIMARY KEY,
                rest_type TEXT NOT NULL CHECK(rest_type IN ('planned', 'recovery', 'life')),
                notes TEXT,
                xp_awarded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Seed all 12 skills
        for skill_name, (domain, virtue, shadow) in SKILL_METADATA.items():
            conn.execute("""
                INSERT OR IGNORE INTO player_skills
                (skill_name, domain, virtue, shadow_warning, current_xp, current_level)
                VALUES (?, ?, ?, ?, 0, 1)
            """, (skill_name, domain, virtue, shadow))

    def _migrate_to_12_skills(self, conn: sqlite3.Connection):
        """Migrate from old 7-skill schema to new 12-skill schema."""
        # Add new columns if they don't exist
        try:
            conn.execute("ALTER TABLE player_skills ADD COLUMN domain TEXT DEFAULT 'body'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE player_skills ADD COLUMN virtue TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE player_skills ADD COLUMN shadow_warning TEXT")
        except sqlite3.OperationalError:
            pass

        # Add failure_tier and notes to xp_events if needed
        try:
            conn.execute("ALTER TABLE xp_events ADD COLUMN failure_tier INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE xp_events ADD COLUMN notes TEXT")
        except sqlite3.OperationalError:
            pass

        # Update existing skills with metadata
        for skill_name, (domain, virtue, shadow) in SKILL_METADATA.items():
            conn.execute("""
                UPDATE player_skills
                SET domain = ?, virtue = ?, shadow_warning = ?
                WHERE skill_name = ?
            """, (domain, virtue, shadow, skill_name))

        # Insert new skills that don't exist
        for skill_name, (domain, virtue, shadow) in SKILL_METADATA.items():
            conn.execute("""
                INSERT OR IGNORE INTO player_skills
                (skill_name, domain, virtue, shadow_warning, current_xp, current_level)
                VALUES (?, ?, ?, ?, 0, 1)
            """, (skill_name, domain, virtue, shadow))

        # Create daily_reflections table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_reflections (
                date DATE PRIMARY KEY,
                prosecution TEXT,
                judgment TEXT,
                advocacy TEXT,
                virtue_focus TEXT,
                virtue_score INTEGER CHECK(virtue_score IS NULL OR (virtue_score >= 1 AND virtue_score <= 10)),
                memento_mori_complete BOOLEAN DEFAULT FALSE,
                xp_awarded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Octalysis-informed streak forgiveness tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS streak_freezes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                earned_at DATE NOT NULL,
                used_at DATE,
                expired BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategic_rest (
                date DATE PRIMARY KEY,
                rest_type TEXT NOT NULL CHECK(rest_type IN ('planned', 'recovery', 'life')),
                notes TEXT,
                xp_awarded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Remove old skills that are no longer in the framework
        old_skills = {'recovery', 'work'}
        for old_skill in old_skills:
            # Check if skill exists and has XP - migrate to appropriate new skill
            cursor = conn.execute(
                "SELECT current_xp FROM player_skills WHERE skill_name = ?",
                (old_skill,)
            )
            row = cursor.fetchone()
            if row and row[0] > 0:
                # Migrate XP: recovery -> endurance, work -> creation
                target_skill = "endurance" if old_skill == "recovery" else "creation"
                conn.execute("""
                    UPDATE player_skills
                    SET current_xp = current_xp + ?
                    WHERE skill_name = ?
                """, (row[0], target_skill))
                logger.info(f"Migrated {row[0]} XP from {old_skill} to {target_skill}")

            # Delete old skill
            conn.execute("DELETE FROM player_skills WHERE skill_name = ?", (old_skill,))

        logger.info("Migration to 12-skill framework complete")

    def set_level_up_callback(self, callback: Callable[[XPAwardResult], None]):
        """Set callback for level-up events (e.g., voice announcement)."""
        self._level_up_callback = callback

    def _normalize_skill(self, skill_name: str) -> str:
        """Normalize skill name to lowercase, validate against enum."""
        normalized = skill_name.lower().strip()
        try:
            SkillName(normalized)
            return normalized
        except ValueError:
            raise ValueError(f"Invalid skill name: {skill_name}. Valid: {[s.value for s in SkillName]}")

    def _get_streak_bonus(self) -> int:
        """Get current streak bonus multiplier (0-14)."""
        conn = self._get_conn()
        today = date.today()
        try:
            cursor = conn.execute("""
                SELECT streak_day FROM activity_streaks
                WHERE date = ?
            """, (today.isoformat(),))
            row = cursor.fetchone()
            if row:
                return min(row["streak_day"], MAX_STREAK_DAYS)

            # Check yesterday for streak continuation
            yesterday = date.today().isoformat()  # Will fix below
            from datetime import timedelta
            yesterday = (today - timedelta(days=1)).isoformat()
            cursor = conn.execute("""
                SELECT streak_day FROM activity_streaks
                WHERE date = ?
            """, (yesterday,))
            row = cursor.fetchone()
            if row:
                new_streak = min(row["streak_day"] + 1, MAX_STREAK_DAYS)
            else:
                new_streak = 1

            # Record today's streak
            conn.execute("""
                INSERT OR REPLACE INTO activity_streaks (date, streak_day, activities_logged)
                VALUES (?, ?, 1)
            """, (today.isoformat(), new_streak))
            conn.commit()
            return new_streak

        except sqlite3.Error as e:
            logger.warning(f"Streak calculation failed: {e}")
            return 0

    def award_xp(
        self,
        skill_name: str,
        base_xp: int,
        source: str,
        apply_streak_bonus: bool = True,
    ) -> XPAwardResult:
        """
        Award XP to a skill (blocking).

        Args:
            skill_name: Target skill (strength, mobility, etc.)
            base_xp: Base XP amount (before bonuses)
            source: Source identifier (workout_strength, morning_routine, etc.)
            apply_streak_bonus: Whether to apply streak multiplier

        Returns:
            XPAwardResult with level-up info

        Raises:
            ValueError: Invalid skill name
            sqlite3.Error: Database error
        """
        skill_name = self._normalize_skill(skill_name)

        # Calculate streak bonus
        streak_bonus_xp = 0
        if apply_streak_bonus:
            streak_days = self._get_streak_bonus()
            streak_bonus_xp = streak_days * XP_TABLE.get("streak_bonus", 5)

        total_xp = base_xp + streak_bonus_xp

        conn = self._get_conn()
        try:
            # Begin transaction
            conn.execute("BEGIN IMMEDIATE")

            # Get current state
            cursor = conn.execute("""
                SELECT current_xp, current_level FROM player_skills
                WHERE skill_name = ?
            """, (skill_name,))
            row = cursor.fetchone()

            if not row:
                # Skill should exist from seed data, but handle edge case
                conn.execute("""
                    INSERT INTO player_skills (skill_name, current_xp, current_level)
                    VALUES (?, 0, 1)
                """, (skill_name,))
                old_xp, old_level = 0, 1
            else:
                old_xp, old_level = row["current_xp"], row["current_level"]

            # Calculate new XP (capped)
            new_xp = min(old_xp + total_xp, MAX_XP_PER_SKILL)
            new_level = level_for_xp(new_xp)
            leveled_up = new_level > old_level

            # Update skill
            conn.execute("""
                UPDATE player_skills
                SET current_xp = ?, current_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE skill_name = ?
            """, (new_xp, new_level, skill_name))

            # Log event
            conn.execute("""
                INSERT INTO xp_events (skill_name, xp_gained, source_type, streak_bonus)
                VALUES (?, ?, ?, ?)
            """, (skill_name, total_xp, source, streak_bonus_xp))

            conn.commit()

            result = XPAwardResult(
                skill_name=skill_name,
                xp_awarded=total_xp,
                new_total_xp=new_xp,
                old_level=old_level,
                new_level=new_level,
                leveled_up=leveled_up,
                source=source,
            )

            logger.info(
                f"Awarded {total_xp} XP to {skill_name} (source={source}). "
                f"Level: {old_level} -> {new_level}"
            )

            # Fire callback if level up
            if leveled_up and self._level_up_callback:
                try:
                    self._level_up_callback(result)
                except Exception as e:
                    logger.warning(f"Level-up callback failed: {e}")

            return result

        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"XP award failed: {e}")
            raise

    def award_xp_async(
        self,
        skill_name: str,
        base_xp: int,
        source: str,
        apply_streak_bonus: bool = True,
    ) -> None:
        """
        Award XP asynchronously (non-blocking).

        For use in voice pipeline where latency matters.
        Failures are logged but don't propagate.

        Args:
            skill_name: Target skill
            base_xp: Base XP amount
            source: Source identifier
            apply_streak_bonus: Whether to apply streak multiplier
        """
        def _do_award():
            try:
                self.award_xp(skill_name, base_xp, source, apply_streak_bonus)
            except Exception as e:
                logger.error(f"Async XP award failed: {e}")

        self._executor.submit(_do_award)

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a single skill's current state."""
        skill_name = self._normalize_skill(skill_name)
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT skill_name, current_xp, current_level, domain, virtue, shadow_warning
                FROM player_skills WHERE skill_name = ?
            """, (skill_name,))
            row = cursor.fetchone()
            if row:
                return Skill(
                    name=row["skill_name"],
                    xp=row["current_xp"],
                    level=row["current_level"],
                    domain=row["domain"] or "body",
                    virtue=row["virtue"] or "",
                    shadow_warning=row["shadow_warning"] or "",
                )
            return None
        except sqlite3.Error as e:
            logger.error(f"Failed to get skill {skill_name}: {e}")
            return None

    def get_all_skills(self) -> List[Skill]:
        """Get all skills ordered by level (descending)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT skill_name, current_xp, current_level, domain, virtue, shadow_warning
                FROM player_skills
                ORDER BY current_level DESC, current_xp DESC
            """)
            return [
                Skill(
                    name=row["skill_name"],
                    xp=row["current_xp"],
                    level=row["current_level"],
                    domain=row["domain"] or "body",
                    virtue=row["virtue"] or "",
                    shadow_warning=row["shadow_warning"] or "",
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            logger.error(f"Failed to get skills: {e}")
            return []

    def get_skills_by_domain(self, domain: str) -> List[Skill]:
        """Get all skills in a specific domain (body/mind/soul)."""
        if domain not in ("body", "mind", "soul"):
            raise ValueError(f"Invalid domain: {domain}. Must be body, mind, or soul.")
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT skill_name, current_xp, current_level, domain, virtue, shadow_warning
                FROM player_skills
                WHERE domain = ?
                ORDER BY current_level DESC, current_xp DESC
            """, (domain,))
            return [
                Skill(
                    name=row["skill_name"],
                    xp=row["current_xp"],
                    level=row["current_level"],
                    domain=row["domain"] or domain,
                    virtue=row["virtue"] or "",
                    shadow_warning=row["shadow_warning"] or "",
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            logger.error(f"Failed to get skills for domain {domain}: {e}")
            return []

    def get_total_level(self) -> int:
        """Get sum of all skill levels."""
        skills = self.get_all_skills()
        return sum(s.level for s in skills)

    def get_combat_level(self) -> int:
        """
        Get OSRS-style combat level.

        Formula: combat_level = (sum_of_all_skill_levels // 2) + 3

        This creates a familiar OSRS feel where 2 skill levels = 1 combat level.
        Starting at level 3, capped at 126 for authenticity.
        """
        total_skill_levels = self.get_total_level()
        return calculate_combat_level_from_total(total_skill_levels)

    def get_skills_to_next_combat_level(self) -> int:
        """Get number of skill levels needed to reach next combat level."""
        total_skill_levels = self.get_total_level()
        return skills_to_next_combat_level(total_skill_levels)

    def get_total_xp(self) -> int:
        """Get sum of all XP across skills."""
        skills = self.get_all_skills()
        return sum(s.xp for s in skills)

    def get_today_xp(self) -> int:
        """Get XP earned today across all skills."""
        conn = self._get_conn()
        today = date.today().isoformat()
        try:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(xp_gained), 0) as total
                FROM xp_events
                WHERE DATE(created_at) = ?
            """, (today,))
            row = cursor.fetchone()
            return row["total"] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Failed to get today's XP: {e}")
            return 0

    def get_current_streak(self) -> int:
        """Get current activity streak in days."""
        conn = self._get_conn()
        today = date.today()
        try:
            cursor = conn.execute("""
                SELECT streak_day FROM activity_streaks
                WHERE date = ?
            """, (today.isoformat(),))
            row = cursor.fetchone()
            if row:
                return row["streak_day"]

            # Check if yesterday had activity (streak not yet updated today)
            from datetime import timedelta
            yesterday = (today - timedelta(days=1)).isoformat()
            cursor = conn.execute("""
                SELECT streak_day FROM activity_streaks
                WHERE date = ?
            """, (yesterday,))
            row = cursor.fetchone()
            return row["streak_day"] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Failed to get streak: {e}")
            return 0

    # ==========================================================================
    # OCTALYSIS STREAK FORGIVENESS SYSTEM
    # From research: "Give users permission to be human rather than demanding
    # algorithmic perfection"
    # ==========================================================================

    def get_rolling_window_consistency(self) -> tuple[int, int]:
        """
        Get rolling window consistency (Octalysis alternative to streaks).

        Returns:
            Tuple of (active_days, required_days) - e.g., (5, 7) means 5 of 7

        From research: "5 of the last 7 days creates accountability without
        catastrophic loss. A single missed day doesn't destroy weeks of progress."
        """
        conn = self._get_conn()
        from datetime import timedelta
        today = date.today()

        try:
            # Count active days in last 7 days
            start_date = (today - timedelta(days=ROLLING_WINDOW_DAYS - 1)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT date) as active_days
                FROM activity_streaks
                WHERE date >= ?
            """, (start_date,))
            row = cursor.fetchone()
            active_days = row["active_days"] if row else 0

            return active_days, ROLLING_WINDOW_DAYS
        except sqlite3.Error as e:
            logger.error(f"Failed to get rolling window: {e}")
            return 0, ROLLING_WINDOW_DAYS

    def is_consistent_rolling_window(self) -> bool:
        """
        Check if user meets rolling window threshold.

        Returns True if 5+ of last 7 days had activity.
        This is the ethical alternative to strict streak counting.
        """
        active, total = self.get_rolling_window_consistency()
        return active >= ROLLING_WINDOW_THRESHOLD

    def get_available_streak_freezes(self) -> int:
        """Get number of unused streak freezes."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM streak_freezes
                WHERE used_at IS NULL AND expired = FALSE
            """)
            row = cursor.fetchone()
            return min(row["count"] if row else 0, MAX_STREAK_FREEZES)
        except sqlite3.Error as e:
            logger.error(f"Failed to get streak freezes: {e}")
            return 0

    def earn_streak_freeze(self) -> bool:
        """
        Award a streak freeze for 7 consecutive days of activity.

        From research: "Users can stack multiple freezes as buffers."

        Returns:
            True if freeze was awarded, False if at max or error
        """
        if self.get_available_streak_freezes() >= MAX_STREAK_FREEZES:
            logger.debug("Already at max streak freezes")
            return False

        conn = self._get_conn()
        today = date.today()

        try:
            # Check if we're at a 7-day boundary
            cursor = conn.execute("""
                SELECT streak_day FROM activity_streaks
                WHERE date = ?
            """, (today.isoformat(),))
            row = cursor.fetchone()

            if row and row["streak_day"] % 7 == 0:
                conn.execute("""
                    INSERT INTO streak_freezes (earned_at)
                    VALUES (?)
                """, (today.isoformat(),))
                conn.commit()
                logger.info(f"Earned streak freeze at day {row['streak_day']}")
                return True

            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to earn streak freeze: {e}")
            return False

    def use_streak_freeze(self, reason: str = "life") -> bool:
        """
        Use a streak freeze to prevent streak break.

        From research: "Safety nets that prevent users from feeling trapped
        by their own success."

        Args:
            reason: Why freeze was used (life, recovery, planned)

        Returns:
            True if freeze was used successfully
        """
        if self.get_available_streak_freezes() <= 0:
            logger.warning("No streak freezes available")
            return False

        conn = self._get_conn()
        today = date.today()

        try:
            # Use oldest freeze first
            conn.execute("""
                UPDATE streak_freezes
                SET used_at = ?
                WHERE id = (
                    SELECT id FROM streak_freezes
                    WHERE used_at IS NULL AND expired = FALSE
                    ORDER BY earned_at ASC
                    LIMIT 1
                )
            """, (today.isoformat(),))
            conn.commit()

            # Award flexibility bonus (counters rigidity shadow)
            self.award_xp("consistency", XP_TABLE.get("flexibility_bonus", 25),
                         "flexibility_bonus", apply_streak_bonus=False)

            logger.info(f"Used streak freeze for reason: {reason}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to use streak freeze: {e}")
            return False

    def log_strategic_rest(
        self,
        rest_type: str = "planned",
        notes: Optional[str] = None
    ) -> int:
        """
        Log a strategic rest day (Octalysis shadow counter).

        From research: "Celebrate strategic rest rather than just persistence.
        The system should acknowledge that recovery is part of training."

        Args:
            rest_type: 'planned', 'recovery', or 'life'
            notes: Optional notes about the rest

        Returns:
            XP awarded for strategic rest
        """
        conn = self._get_conn()
        today = date.today()

        xp_source = f"strategic_rest_{rest_type}"
        xp_amount = XP_TABLE.get(xp_source, 30)

        try:
            conn.execute("""
                INSERT OR REPLACE INTO strategic_rest
                (date, rest_type, notes, xp_awarded)
                VALUES (?, ?, ?, ?)
            """, (today.isoformat(), rest_type, notes, xp_amount))
            conn.commit()

            # Award to Consistency skill (rest IS consistency)
            self.award_xp("consistency", xp_amount, xp_source, apply_streak_bonus=False)

            # If planned rest, also award to Endurance (recovery = grit)
            if rest_type == "recovery":
                endurance_xp = XP_TABLE.get("rest_day", 50)
                self.award_xp("endurance", endurance_xp, "rest_day", apply_streak_bonus=False)

            logger.info(f"Logged strategic rest ({rest_type}): {xp_amount} XP")
            return xp_amount
        except sqlite3.Error as e:
            logger.error(f"Failed to log strategic rest: {e}")
            return 0

    def get_streak_status_voice(self) -> str:
        """
        Get comprehensive streak status for voice output.

        Includes both traditional streak and rolling window,
        emphasizing the ethical framing from Octalysis.
        """
        streak = self.get_current_streak()
        active, total = self.get_rolling_window_consistency()
        freezes = self.get_available_streak_freezes()

        parts = []

        # Streak info
        if streak > 0:
            parts.append(f"{streak} day streak")

        # Rolling window (the ethical alternative)
        if active >= ROLLING_WINDOW_THRESHOLD:
            parts.append(f"{active} of {total} days active")
        elif active > 0:
            needed = ROLLING_WINDOW_THRESHOLD - active
            parts.append(f"{active} of {total} days, {needed} more for consistency")

        # Freezes available (safety net)
        if freezes > 0:
            parts.append(f"{freezes} streak {'freeze' if freezes == 1 else 'freezes'} saved")

        if not parts:
            return "Start your consistency journey today."

        return ". ".join(parts) + "."

    def reconcile(self) -> Tuple[bool, dict]:
        """
        Verify XP totals match event sums.

        Returns:
            Tuple of (is_valid, discrepancies_dict)
        """
        conn = self._get_conn()
        discrepancies = {}
        try:
            # Get stored totals
            cursor = conn.execute("""
                SELECT skill_name, current_xp FROM player_skills
            """)
            stored = {row["skill_name"]: row["current_xp"] for row in cursor.fetchall()}

            # Get calculated totals from events
            cursor = conn.execute("""
                SELECT skill_name, SUM(xp_gained) as total
                FROM xp_events
                GROUP BY skill_name
            """)
            calculated = {row["skill_name"]: row["total"] for row in cursor.fetchall()}

            # Compare
            for skill_name, stored_xp in stored.items():
                calc_xp = calculated.get(skill_name, 0)
                if stored_xp != calc_xp:
                    discrepancies[skill_name] = {
                        "stored": stored_xp,
                        "calculated": calc_xp,
                        "diff": stored_xp - calc_xp,
                    }

            is_valid = len(discrepancies) == 0
            if not is_valid:
                logger.warning(f"XP reconciliation found discrepancies: {discrepancies}")

            return is_valid, discrepancies

        except sqlite3.Error as e:
            logger.error(f"Reconciliation failed: {e}")
            return False, {"error": str(e)}

    def format_status_voice(self) -> str:
        """Format skill status for voice output."""
        skills = self.get_all_skills()
        if not skills:
            return "No skill data available."

        # Get top 3 skills
        top_skills = skills[:3]
        parts = []

        for skill in top_skills:
            parts.append(f"{skill.name.title()} {skill.level}")

        total = self.get_total_level()
        today = self.get_today_xp()
        streak = self.get_current_streak()

        response = f"Total level {total}. {', '.join(parts)}."
        if today > 0:
            response += f" {today:,} XP today."
        if streak > 1:
            response += f" {streak} day streak."

        return response

    def format_status_voice_with_titles(self) -> str:
        """
        Format skill status with Octalysis titles.

        From research: "Achievement names should evoke transformation and
        mastery rather than generic labels."
        """
        skills = self.get_all_skills()
        if not skills:
            return "No skill data available."

        # Get top 3 skills with titles
        top_skills = skills[:3]
        parts = []

        for skill in top_skills:
            parts.append(f"{skill.name.title()} {skill.level} {skill.title}")

        total = self.get_total_level()
        today = self.get_today_xp()

        response = f"Total level {total}. {', '.join(parts)}."
        if today > 0:
            response += f" {today:,} XP today."

        # Add rolling window instead of streak (ethical framing)
        active, total_days = self.get_rolling_window_consistency()
        if active >= ROLLING_WINDOW_THRESHOLD:
            response += f" Consistent: {active} of {total_days} days."
        elif active > 0:
            response += f" {active} of {total_days} days active."

        return response

    def get_graduation_status(self, skill_name: str) -> Optional[str]:
        """
        Check if skill is ready for "graduation" (reduced tracking).

        From research: "The highest success isn't a five-year streak—it's a
        user who developed such deep habits they no longer need external tracking."

        Returns message about graduation eligibility, or None if not ready.
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return None

        # Graduation thresholds based on Octalysis research
        if skill.level >= 76:  # Master tier
            return (
                f"{skill.name.title()} is at Master level ({skill.level}). "
                f"Consider transitioning to maintenance mode—weekly check-ins "
                f"instead of daily tracking. The habit is internalized."
            )
        elif skill.level >= 56:  # Adept tier
            return (
                f"{skill.name.title()} approaching mastery ({skill.level}). "
                f"The scaffolding has served its purpose. Trust the habit."
            )

        return None

    def format_domain_status_voice(self, domain: str) -> str:
        """Format status for a single domain (body/mind/soul)."""
        skills = self.get_skills_by_domain(domain)
        if not skills:
            return f"No {domain} skills available."

        parts = [f"{s.name.title()} {s.level}" for s in skills]
        domain_total = sum(s.level for s in skills)

        return f"{domain.title()} level {domain_total}. {', '.join(parts)}."

    def log_reflection(
        self,
        prosecution: Optional[str] = None,
        judgment: Optional[str] = None,
        advocacy: Optional[str] = None,
        virtue_focus: Optional[str] = None,
        virtue_score: Optional[int] = None,
        memento_mori: bool = False,
    ) -> int:
        """
        Log a daily reflection (Seneca's Trial).

        Returns XP awarded for the reflection.
        """
        conn = self._get_conn()
        today = date.today().isoformat()
        xp_awarded = 0

        try:
            # Calculate XP for reflection components
            if prosecution and judgment and advocacy:
                xp_awarded += XP_TABLE.get("evening_audit", 60)
            elif prosecution or judgment or advocacy:
                xp_awarded += XP_TABLE.get("journal_entry", 35)

            if memento_mori:
                xp_awarded += XP_TABLE.get("memento_mori", 25)

            # Insert or update reflection
            conn.execute("""
                INSERT INTO daily_reflections
                (date, prosecution, judgment, advocacy, virtue_focus, virtue_score,
                 memento_mori_complete, xp_awarded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    prosecution = COALESCE(excluded.prosecution, prosecution),
                    judgment = COALESCE(excluded.judgment, judgment),
                    advocacy = COALESCE(excluded.advocacy, advocacy),
                    virtue_focus = COALESCE(excluded.virtue_focus, virtue_focus),
                    virtue_score = COALESCE(excluded.virtue_score, virtue_score),
                    memento_mori_complete = excluded.memento_mori_complete OR memento_mori_complete,
                    xp_awarded = xp_awarded + excluded.xp_awarded
            """, (today, prosecution, judgment, advocacy, virtue_focus,
                  virtue_score, memento_mori, xp_awarded))

            conn.commit()

            # Award XP to reflection skill
            if xp_awarded > 0:
                self.award_xp("reflection", xp_awarded, "evening_audit")

            return xp_awarded

        except sqlite3.Error as e:
            logger.error(f"Failed to log reflection: {e}")
            return 0

    def get_reflection_streak(self) -> int:
        """Get current reflection streak (consecutive days with complete reflections)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) as streak
                FROM (
                    SELECT date,
                           julianday(date) - ROW_NUMBER() OVER (ORDER BY date) as grp
                    FROM daily_reflections
                    WHERE advocacy IS NOT NULL
                    AND date <= DATE('now')
                )
                GROUP BY grp
                ORDER BY MAX(date) DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Failed to get reflection streak: {e}")
            return 0

    def close(self):
        """Close database connection and executor."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
        self._executor.shutdown(wait=False)


# Fail-safe wrapper for use in health services
def award_xp_safe(
    skill_name: str,
    base_xp: int,
    source: str,
    apply_streak_bonus: bool = True,
) -> Optional[XPAwardResult]:
    """
    Safely award XP without raising exceptions.

    For use in health services where XP failure should not
    break core functionality.

    Returns:
        XPAwardResult on success, None on failure
    """
    try:
        from atlas.gamification import get_xp_service
        service = get_xp_service()
        return service.award_xp(skill_name, base_xp, source, apply_streak_bonus)
    except Exception as e:
        logger.warning(f"XP award failed (non-fatal): {e}")
        return None


def award_xp_safe_async(
    skill_name: str,
    base_xp: int,
    source: str,
    apply_streak_bonus: bool = True,
) -> None:
    """
    Safely award XP asynchronously without blocking.

    For use in voice pipeline where latency matters.
    """
    try:
        from atlas.gamification import get_xp_service
        service = get_xp_service()
        service.award_xp_async(skill_name, base_xp, source, apply_streak_bonus)
    except Exception as e:
        logger.warning(f"Async XP award setup failed (non-fatal): {e}")


# CLI for testing
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="XP Service CLI (12-Skill Lethal Gentleman Framework)")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--status", action="store_true", help="Show skill status")
    parser.add_argument("--domain", choices=["body", "mind", "soul"], help="Show skills for domain")
    parser.add_argument("--award", nargs=3, metavar=("SKILL", "XP", "SOURCE"),
                        help="Award XP to skill")
    parser.add_argument("--reconcile", action="store_true", help="Check XP integrity")
    parser.add_argument("--migrate", action="store_true", help="Force migration to 12-skill schema")
    args = parser.parse_args()

    service = XPService()

    if args.test:
        print("XP Service Self-Test (12-Skill Framework)")
        print("=" * 50)

        # Test award
        result = service.award_xp("strength", 100, "test_cli")
        print(f"Awarded 100 XP to strength: Level {result.old_level} -> {result.new_level}")

        # Test get all by domain
        for domain in ["body", "mind", "soul"]:
            skills = service.get_skills_by_domain(domain)
            print(f"\n{domain.upper()} ({len(skills)} skills):")
            for skill in skills:
                print(f"  {skill.name:12} | {skill.virtue:20} | Level {skill.level}")

        # Test reconcile
        valid, disc = service.reconcile()
        print(f"\nReconciliation: {'PASS' if valid else 'FAIL'}")
        if disc:
            print(f"  Discrepancies: {disc}")

        print("\nVoice output:")
        print(f"  {service.format_status_voice()}")

    elif args.status:
        print(service.format_status_voice())
        print()
        print("=" * 60)

        for domain in ["body", "mind", "soul"]:
            skills = service.get_skills_by_domain(domain)
            domain_total = sum(s.level for s in skills)
            print(f"\n{domain.upper()} (Level {domain_total})")
            print("-" * 60)
            for skill in skills:
                pct = skill.progress_pct
                bar = "=" * int(pct / 5) + "-" * (20 - int(pct / 5))
                print(f"  {skill.name:12} Lv{skill.level:2d} [{bar}] {pct:5.1f}%  {skill.virtue}")

    elif args.domain:
        skills = service.get_skills_by_domain(args.domain)
        print(service.format_domain_status_voice(args.domain))
        print()
        for skill in skills:
            pct = skill.progress_pct
            bar = "=" * int(pct / 5) + "-" * (20 - int(pct / 5))
            print(f"  {skill.name:12} Level {skill.level:2d} [{bar}] {pct:.1f}%")
            print(f"    Virtue: {skill.virtue}")
            print(f"    Shadow: {skill.shadow_warning}")
            print()

    elif args.award:
        skill, xp, source = args.award
        result = service.award_xp(skill, int(xp), source)
        print(f"Awarded {result.xp_awarded} XP to {result.skill_name}")
        if result.leveled_up:
            print(result.level_up_message())

    elif args.reconcile:
        valid, disc = service.reconcile()
        print(f"Reconciliation: {'PASS' if valid else 'FAIL'}")
        if disc:
            for skill, info in disc.items():
                print(f"  {skill}: stored={info['stored']}, calculated={info['calculated']}, diff={info['diff']}")

    elif args.migrate:
        print("Forcing migration to 12-skill schema...")
        # Just reinitializing will trigger migration if needed
        print("Migration complete. Run --status to verify.")

    else:
        parser.print_help()

    service.close()
