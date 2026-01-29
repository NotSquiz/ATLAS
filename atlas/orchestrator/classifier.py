"""
ATLAS Thought Classifier

Removes taxonomy work at capture time by automatically classifying
raw thoughts into structured categories.

Categories (from "2nd Brain" video):
- People: Relationships, follow-ups, who someone is
- Projects: Active work with next actions
- Ideas: Insights, one-liners, creative thoughts
- Admin: Tasks with due dates, logistics

The classifier extracts structured fields per category and routes
to appropriate storage.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from atlas.memory.store import get_store

logger = logging.getLogger(__name__)


class Category(Enum):
    """Thought categories."""
    PEOPLE = "people"
    PROJECTS = "projects"
    IDEAS = "ideas"
    ADMIN = "admin"
    RECIPES = "recipes"
    UNKNOWN = "unknown"


@dataclass
class PersonRecord:
    """Structured record for a person."""
    name: str
    context: Optional[str] = None  # Who they are, how you know them
    follow_ups: list[str] = field(default_factory=list)
    last_touched: Optional[date] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class ProjectRecord:
    """Structured record for a project with optional hierarchy."""
    name: str
    parent_project: Optional[str] = None  # e.g., "baby-brains", "health"
    sub_area: Optional[str] = None  # e.g., "website", "sauna"
    status: str = "active"  # active, waiting, blocked, someday, done
    next_action: Optional[str] = None  # Specific, executable action
    notes: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class IdeaRecord:
    """Structured record for an idea."""
    name: str
    one_liner: Optional[str] = None  # Core insight
    notes: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AdminRecord:
    """Structured record for admin task."""
    name: str
    due_date: Optional[date] = None
    status: str = "pending"  # pending, done
    notes: Optional[str] = None


@dataclass
class RecipeRecord:
    """Structured record for a recipe."""
    name: str
    notes: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Result of thought classification."""
    category: Category
    confidence: float
    original_text: str
    record: Optional[PersonRecord | ProjectRecord | IdeaRecord | AdminRecord | RecipeRecord] = None
    filed_to: Optional[str] = None  # Where it was stored
    memory_id: Optional[int] = None


class ThoughtClassifier:
    """
    Classifies raw thoughts into structured categories.

    Uses pattern matching for fast classification (no LLM required).
    Can optionally use LLM for complex cases.

    Usage:
        classifier = ThoughtClassifier()

        result = classifier.classify("Call Sarah about the project deadline")
        print(result.category)  # Category.PEOPLE
        print(result.record)    # PersonRecord(name="Sarah", ...)

        # Classify and store
        result = classifier.classify_and_store("New idea: AI-powered meal planning")
    """

    # Pattern-based classification (fast, no LLM)
    PEOPLE_PATTERNS = [
        r"\bcall\b.*\b(\w+)\b",
        r"\bemail\b.*\b(\w+)\b",
        r"\bmeet(?:ing)?\s+(?:with\s+)?(\w+)",
        r"\b(\w+)\s+(?:said|mentioned|told|asked)",
        r"\bfollow[- ]?up\s+(?:with\s+)?(\w+)",
        r"\bcheck[- ]?in\s+(?:with\s+)?(\w+)",
        r"\bremember\s+(?:that\s+)?(\w+)",
        r"\b(\w+)'s\s+(?:birthday|anniversary)",
        r"\btalk\s+to\s+(\w+)",
    ]

    PROJECT_PATTERNS = [
        r"\bproject\b",
        r"\blaunch\b",
        r"\bbuild\b",
        r"\bcreate\b",
        r"\bdevelop\b",
        r"\bimplement\b",
        r"\bship\b",
        r"\brelease\b",
        r"\bmilestone\b",
        r"\bdeadline\b",
        r"\bsprint\b",
        r"\bphase\b",
        r"\bv\d+",  # Version numbers
        r"\bnext\s+step",
        r"\baction\s+item",
        r"\bblocked\s+(?:by|on)",
        r"\bwaiting\s+(?:for|on)",
    ]

    IDEA_PATTERNS = [
        r"\bidea\b",
        r"\bwhat\s+if\b",
        r"\binsight\b",
        r"\brealization\b",
        r"\bthought\b",
        r"\bconcept\b",
        r"\bhypothesis\b",
        r"\bpossibility\b",
        r"\bcould\s+(?:we|I|you)\b",
        r"\bmaybe\s+(?:we|I)\b",
        r"\bimagine\b",
        r"\bbrainstorm\b",
    ]

    ADMIN_PATTERNS = [
        r"\bdue\b",
        r"\bdeadline\b",
        r"\bby\s+(?:end\s+of\s+)?(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        r"\bpay\b",
        r"\bbill\b",
        r"\brenew\b",
        r"\bexpir(?:e|ing|es)\b",
        r"\bappointment\b",
        r"\bschedule\b",
        r"\bbook\b",
        r"\breserv(?:e|ation)\b",
        r"\breminder\b",
        r"\bdon't\s+forget\b",
    ]

    RECIPE_PATTERNS = [
        r"\brecipe\b",
        r"\bcooked?\b",
        r"\bmade\b.*\b(?:dinner|lunch|breakfast|meal)\b",
        r"\bingredients?\b",
        r"\bcuisine\b",
    ]

    # Project taxonomy for hierarchical classification
    PROJECT_TAXONOMY = {
        "baby-brains": {
            "patterns": [r"\bbaby\s*brains?\b", r"\bbb\b"],
            "areas": {
                "website": [r"\bweb(?:site)?\b", r"\blanding\s+page\b", r"\bnext\.?js\b", r"\bsupabase\b"],
                "app": [r"\bapp\b", r"\bmobile\b", r"\bios\b", r"\bandroid\b"],
                "knowledge": [r"\bknowledge\b", r"\bgraph\b", r"\batoms?\b", r"\byaml\b", r"\bcanonical\b"],
                "os": [r"\bos\b", r"\bmarketing\s+agent\b", r"\bskills?\b", r"\bbabybrains-os\b"],
                "marketing": [r"\bmarketing\b", r"\bcontent\b", r"\bsocial\b", r"\bvideo\b", r"\btiktok\b", r"\breels?\b"],
                "content": [r"\bcontent\s+creation\b", r"\bshort[- ]?form\b"],
            }
        },
        "health": {
            "patterns": [r"\bhealth\b", r"\bdiy\b", r"\bfitness\b", r"\bbody\b", r"\bwellness\b"],
            "areas": {
                "sauna": [r"\bsauna\b"],
                "red-light": [r"\bred\s*light\b", r"\bpanel\b", r"\btherapy\s+light\b"],
                "garmin": [r"\bgarmin\b", r"\bwatch\b", r"\btracker\b", r"\bhrv\b", r"\bfitbit\b"],
                "workouts": [r"\bworkout\b", r"\bexercise\b", r"\bgym\b", r"\blifting\b", r"\bstrength\b"],
                "ice-bath": [r"\bice\s*bath\b", r"\bcold\s*(?:plunge|therapy|exposure)\b", r"\bcold\s+water\b"],
                "running": [r"\brunning\b", r"\brun\b", r"\bjog\b", r"\bmarathon\b", r"\b5k\b", r"\b10k\b"],
                "meals": [r"\bmeal\b", r"\bfood\s*(?:log|track)\b", r"\bcalories?\b", r"\bmacros?\b", r"\bnutrition\b"],
            }
        },
    }

    # Common names to recognize (Australian context)
    COMMON_NAMES = {
        "sarah", "emma", "olivia", "charlotte", "amelia", "isla",
        "james", "william", "oliver", "jack", "noah", "leo",
        "mum", "dad", "mom", "father", "mother", "partner",
    }

    def __init__(self):
        """Initialize the classifier."""
        self.store = get_store()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self._people_re = [re.compile(p, re.IGNORECASE) for p in self.PEOPLE_PATTERNS]
        self._project_re = [re.compile(p, re.IGNORECASE) for p in self.PROJECT_PATTERNS]
        self._idea_re = [re.compile(p, re.IGNORECASE) for p in self.IDEA_PATTERNS]
        self._admin_re = [re.compile(p, re.IGNORECASE) for p in self.ADMIN_PATTERNS]
        self._recipe_re = [re.compile(p, re.IGNORECASE) for p in self.RECIPE_PATTERNS]

        # Compile taxonomy patterns
        self._taxonomy_compiled = {}
        for parent, config in self.PROJECT_TAXONOMY.items():
            self._taxonomy_compiled[parent] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in config["patterns"]],
                "areas": {
                    area: [re.compile(p, re.IGNORECASE) for p in patterns]
                    for area, patterns in config["areas"].items()
                }
            }

    def _count_pattern_matches(
        self,
        text: str,
        patterns: list[re.Pattern],
    ) -> tuple[int, list[str]]:
        """Count pattern matches and return captured groups."""
        count = 0
        captures = []
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                count += len(matches)
                # Flatten if needed
                for m in matches:
                    if isinstance(m, tuple):
                        captures.extend(m)
                    else:
                        captures.append(m)
        return count, captures

    def _extract_name(self, text: str, captures: list[str]) -> Optional[str]:
        """Extract a person's name from text or captures."""
        # Check captures first
        for cap in captures:
            if cap.lower() in self.COMMON_NAMES:
                return cap.title()
            # Assume single capitalized words might be names
            if cap.istitle() and len(cap) >= 2:
                return cap

        # Scan text for common names
        words = text.split()
        for word in words:
            clean = word.strip(".,!?;:'\"")
            if clean.lower() in self.COMMON_NAMES:
                return clean.title()

        return None

    def _extract_next_action(self, text: str) -> Optional[str]:
        """Extract next action from project text."""
        # Look for action verbs at start of sentences
        action_verbs = [
            "call", "email", "send", "write", "create", "build",
            "review", "check", "update", "fix", "implement", "design",
            "meet", "discuss", "schedule", "plan", "prepare",
        ]

        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence = sentence.strip()
            first_word = sentence.split()[0].lower() if sentence else ""
            if first_word in action_verbs:
                return sentence[:100]

        # If no explicit action, create one from the text
        return f"Review: {text[:50]}..." if len(text) > 50 else f"Review: {text}"

    def _extract_due_date(self, text: str) -> Optional[date]:
        """Extract due date from admin text."""
        text_lower = text.lower()
        today = date.today()

        # Today/tomorrow (use timedelta to avoid month overflow)
        if "today" in text_lower:
            return today
        if "tomorrow" in text_lower:
            return today + timedelta(days=1)

        # Day of week
        days = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        for day_name, day_num in days.items():
            if day_name in text_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)

        return None

    def _extract_project_hierarchy(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract parent project and sub-area from text using taxonomy.

        Args:
            text: Raw thought text

        Returns:
            Tuple of (parent_project, sub_area) or (None, None) if no match
        """
        text_lower = text.lower()

        for parent, compiled in self._taxonomy_compiled.items():
            # Check if any parent pattern matches
            parent_matched = any(p.search(text_lower) for p in compiled["patterns"])

            if parent_matched:
                # Found parent, now find sub-area
                for area, area_patterns in compiled["areas"].items():
                    if any(p.search(text_lower) for p in area_patterns):
                        return (parent, area)
                # Parent found but no specific area
                return (parent, None)

            # Also check area patterns directly (may imply parent)
            for area, area_patterns in compiled["areas"].items():
                if any(p.search(text_lower) for p in area_patterns):
                    return (parent, area)

        return (None, None)

    def classify(self, text: str) -> ClassificationResult:
        """
        Classify a thought into a category.

        Args:
            text: Raw thought text

        Returns:
            ClassificationResult with category, confidence, and structured record
        """
        text = text.strip()
        if not text:
            return ClassificationResult(
                category=Category.UNKNOWN,
                confidence=0.0,
                original_text=text,
            )

        # Count pattern matches for each category
        people_count, people_caps = self._count_pattern_matches(text, self._people_re)
        project_count, _ = self._count_pattern_matches(text, self._project_re)
        idea_count, _ = self._count_pattern_matches(text, self._idea_re)
        admin_count, _ = self._count_pattern_matches(text, self._admin_re)
        recipe_count, _ = self._count_pattern_matches(text, self._recipe_re)

        # Check for project hierarchy (Baby Brains, Health, etc.)
        parent_project, sub_area = self._extract_project_hierarchy(text)
        if parent_project:
            project_count += 2  # Boost if matches taxonomy

        # Determine winner
        scores = {
            Category.PEOPLE: people_count * 1.2,  # Boost people slightly
            Category.PROJECTS: project_count,
            Category.IDEAS: idea_count,
            Category.ADMIN: admin_count,
            Category.RECIPES: recipe_count * 1.5,  # Boost recipes to avoid false positives
        }

        total = sum(scores.values())
        if total == 0:
            # Default to ideas for uncategorized thoughts
            return ClassificationResult(
                category=Category.IDEAS,
                confidence=0.4,
                original_text=text,
                record=IdeaRecord(
                    name=text[:50],
                    notes=text,
                ),
            )

        winner = max(scores.items(), key=lambda x: x[1])
        confidence = winner[1] / total if total > 0 else 0.5

        # Create structured record based on category
        record = None
        if winner[0] == Category.PEOPLE:
            name = self._extract_name(text, people_caps) or "Unknown"
            record = PersonRecord(
                name=name,
                context=text,
                last_touched=date.today(),
            )
        elif winner[0] == Category.PROJECTS:
            record = ProjectRecord(
                name=text[:50],
                parent_project=parent_project,
                sub_area=sub_area,
                next_action=self._extract_next_action(text),
                notes=text,
            )
        elif winner[0] == Category.IDEAS:
            record = IdeaRecord(
                name=text[:50],
                one_liner=text[:100] if len(text) > 100 else text,
                notes=text if len(text) > 100 else None,
            )
        elif winner[0] == Category.ADMIN:
            record = AdminRecord(
                name=text[:50],
                due_date=self._extract_due_date(text),
                notes=text,
            )
        elif winner[0] == Category.RECIPES:
            record = RecipeRecord(
                name=text[:50],
                notes=text,
            )

        return ClassificationResult(
            category=winner[0],
            confidence=confidence,
            original_text=text,
            record=record,
        )

    def classify_and_store(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> ClassificationResult:
        """
        Classify a thought and store it in memory.

        Args:
            text: Raw thought text
            min_confidence: Minimum confidence to auto-store (default 0.5)

        Returns:
            ClassificationResult with storage info
        """
        result = self.classify(text)

        # Don't store if confidence too low
        if result.confidence < min_confidence:
            logger.info(
                f"Skipping storage: confidence {result.confidence:.2f} < {min_confidence}"
            )
            return result

        # Map category to memory_type
        category_to_type = {
            Category.PEOPLE: "event",  # People interactions are events
            Category.PROJECTS: "event",  # Project updates are events
            Category.IDEAS: "preference",  # Ideas are like preferences
            Category.ADMIN: "event",  # Admin tasks are events
            Category.RECIPES: "preference",  # Recipes are like preferences
            Category.UNKNOWN: "general",
        }

        memory_type = category_to_type.get(result.category, "general")

        # Build hierarchical source field for projects
        if result.category == Category.PROJECTS and isinstance(result.record, ProjectRecord):
            parent = result.record.parent_project or "general"
            sub = result.record.sub_area or ""
            source = f"classifier:projects:{parent}:{sub}".rstrip(":")
        else:
            source = f"classifier:{result.category.value}"

        # Store with appropriate importance
        importance = min(0.5 + (result.confidence * 0.3), 0.9)

        try:
            memory_id = self.store.add_memory(
                content=text,
                importance=importance,
                memory_type=memory_type,
                source=source,
            )

            result.memory_id = memory_id
            result.filed_to = f"semantic_memory (type={memory_type})"

            logger.info(
                f"Stored {result.category.value} with confidence {result.confidence:.2f} "
                f"as memory {memory_id}"
            )

            # Award Work XP for baby-brains project captures (non-blocking)
            if (result.category == Category.PROJECTS and
                isinstance(result.record, ProjectRecord) and
                result.record.parent_project == "baby-brains"):
                self._award_work_xp()

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            result.filed_to = f"FAILED: {str(e)[:50]}"

        return result

    def _award_work_xp(self) -> None:
        """Award Work XP for baby-brains captures (non-blocking)."""
        try:
            from atlas.gamification.xp_service import award_xp_safe_async, XP_TABLE
            xp = XP_TABLE.get("work_capture", 30)
            award_xp_safe_async("work", xp, "work_capture")
        except Exception as e:
            # XP failure should never break thought classification
            logger.debug(f"Work XP award skipped: {e}")

    def to_json(self, result: ClassificationResult) -> str:
        """Convert classification result to JSON."""
        data = {
            "category": result.category.value,
            "confidence": result.confidence,
            "original_text": result.original_text,
            "filed_to": result.filed_to,
            "memory_id": result.memory_id,
        }

        if result.record:
            if isinstance(result.record, PersonRecord):
                data["record"] = {
                    "type": "person",
                    "name": result.record.name,
                    "context": result.record.context,
                    "follow_ups": result.record.follow_ups,
                }
            elif isinstance(result.record, ProjectRecord):
                data["record"] = {
                    "type": "project",
                    "name": result.record.name,
                    "parent_project": result.record.parent_project,
                    "sub_area": result.record.sub_area,
                    "status": result.record.status,
                    "next_action": result.record.next_action,
                }
            elif isinstance(result.record, IdeaRecord):
                data["record"] = {
                    "type": "idea",
                    "name": result.record.name,
                    "one_liner": result.record.one_liner,
                }
            elif isinstance(result.record, AdminRecord):
                data["record"] = {
                    "type": "admin",
                    "name": result.record.name,
                    "due_date": str(result.record.due_date) if result.record.due_date else None,
                    "status": result.record.status,
                }
            elif isinstance(result.record, RecipeRecord):
                data["record"] = {
                    "type": "recipe",
                    "name": result.record.name,
                    "notes": result.record.notes,
                }

        return json.dumps(data, indent=2)


# CLI interface
def main():
    """CLI for thought classification."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Classify thoughts")
    parser.add_argument("text", nargs="?", help="Text to classify")
    parser.add_argument("--store", action="store_true", help="Store in memory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Read from stdin if no text provided
    if args.text:
        text = args.text
    else:
        text = sys.stdin.read().strip()

    if not text:
        print("No text provided")
        sys.exit(1)

    classifier = ThoughtClassifier()

    if args.store:
        result = classifier.classify_and_store(text)
    else:
        result = classifier.classify(text)

    if args.json:
        print(classifier.to_json(result))
    else:
        print(f"Category: {result.category.value}")
        print(f"Confidence: {result.confidence:.2f}")
        if result.record:
            print(f"Record: {result.record}")
        if result.memory_id:
            print(f"Stored as: memory #{result.memory_id}")


if __name__ == "__main__":
    main()
