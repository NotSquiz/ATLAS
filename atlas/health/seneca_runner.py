"""
ATLAS Seneca Trial Runner

Stoic evening reflection protocol based on Seneca's nightly practice.
Two modes: Full (~10 min) and Quick (~3 min).

Full Protocol:
1. Prosecution - "Where did you fall short?"
2. Judgment - "What's the truth of your actions?"
3. Advocacy - "What did you do well?"
4. Tomorrow - Intentions for next day
5. Memento Mori (optional) - Death meditation

Quick Protocol:
1. Brief Review - One win, one improvement
2. Tomorrow - One focus

Usage:
    runner = SenecaRunner()
    response = runner.start()         # Start full trial
    response = runner.start_quick()   # Start quick version
    response = runner.handle_input(text)  # Process user response
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class TrialPhase(Enum):
    """Phases of the Seneca Trial."""
    INACTIVE = "inactive"
    PROSECUTION = "prosecution"
    JUDGMENT = "judgment"
    ADVOCACY = "advocacy"
    TOMORROW = "tomorrow"
    MEMENTO_MORI = "memento_mori"
    COMPLETE = "complete"


@dataclass
class TrialState:
    """State tracking for an active trial."""
    active: bool = False
    is_quick: bool = False
    phase: TrialPhase = TrialPhase.INACTIVE
    phase_index: int = 0
    responses: dict = field(default_factory=dict)
    started_at: Optional[datetime] = None
    memento_mori_asked: bool = False


class SenecaRunner:
    """
    Runner for the Seneca Trial evening reflection protocol.

    Manages state across voice interactions for multi-phase reflections.
    """

    PROTOCOL_PATH = Path(__file__).parent.parent.parent / "config" / "protocols" / "seneca_trial.json"

    def __init__(self):
        self.state = TrialState()
        self._protocol = None
        self._load_protocol()

    def _load_protocol(self):
        """Load protocol definition from JSON."""
        try:
            if self.PROTOCOL_PATH.exists():
                with open(self.PROTOCOL_PATH) as f:
                    self._protocol = json.load(f)
                logger.debug("Loaded Seneca Trial protocol")
            else:
                logger.warning(f"Protocol file not found: {self.PROTOCOL_PATH}")
                self._protocol = self._default_protocol()
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load protocol: {e}")
            self._protocol = self._default_protocol()

    def _default_protocol(self) -> dict:
        """Fallback protocol if JSON not available."""
        return {
            "versions": {
                "full": {
                    "xp_award": 60,
                    "xp_source": "evening_audit",
                    "skill": "reflection",
                    "phases": [
                        {"name": "Prosecution", "voice_prompt": "Where did you fall short today?"},
                        {"name": "Judgment", "voice_prompt": "What's the truth of your actions?"},
                        {"name": "Advocacy", "voice_prompt": "What did you do well?"},
                        {"name": "Tomorrow", "voice_prompt": "What is your one focus for tomorrow?"},
                    ],
                    "closing": "Your trial is complete. Rest well."
                },
                "quick": {
                    "xp_award": 35,
                    "xp_source": "journal_entry",
                    "skill": "reflection",
                    "phases": [
                        {"name": "Brief Review", "voice_prompt": "One thing you did well, one thing to improve."},
                        {"name": "Tomorrow", "voice_prompt": "Your one focus for tomorrow?"},
                    ],
                    "closing": "Noted. Rest well."
                }
            }
        }

    @property
    def is_active(self) -> bool:
        """Check if a trial is currently active."""
        return self.state.active

    def start(self) -> str:
        """Start full Seneca Trial."""
        self.state = TrialState(
            active=True,
            is_quick=False,
            phase=TrialPhase.PROSECUTION,
            phase_index=0,
            started_at=datetime.now()
        )

        version = self._protocol["versions"]["full"]
        first_phase = version["phases"][0]

        return first_phase.get("voice_prompt", first_phase.get("prompt", "Let us begin."))

    def start_quick(self) -> str:
        """Start quick reflection version."""
        self.state = TrialState(
            active=True,
            is_quick=True,
            phase=TrialPhase.PROSECUTION,  # Reuse for first phase
            phase_index=0,
            started_at=datetime.now()
        )

        version = self._protocol["versions"]["quick"]
        first_phase = version["phases"][0]

        return first_phase.get("voice_prompt", first_phase.get("prompt", "Quick reflection."))

    def handle_input(self, text: str) -> str:
        """
        Process user input during active trial.

        Args:
            text: User's spoken response

        Returns:
            Next prompt or closing message
        """
        if not self.state.active:
            return "No active reflection. Say 'start reflection' to begin."

        version_key = "quick" if self.state.is_quick else "full"
        version = self._protocol["versions"][version_key]
        phases = version["phases"]

        # Store current response
        current_phase = phases[self.state.phase_index]
        self.state.responses[current_phase["name"].lower()] = text

        # Move to next phase
        self.state.phase_index += 1

        # Check if we have more phases
        if self.state.phase_index < len(phases):
            next_phase = phases[self.state.phase_index]

            # Check for optional memento mori
            if next_phase.get("optional") and not self.state.is_quick:
                self.state.memento_mori_asked = True
                return (
                    f"{next_phase.get('voice_prompt', '')} "
                    "This is optional. Say 'skip' to finish, or reflect on mortality."
                )

            return next_phase.get("voice_prompt", next_phase.get("prompt", "Continue."))
        else:
            # Trial complete
            return self._complete_trial(version)

    def handle_skip(self) -> str:
        """Handle skip command during optional phases."""
        if not self.state.active:
            return "No active reflection."

        return self._complete_trial(
            self._protocol["versions"]["quick" if self.state.is_quick else "full"]
        )

    def _complete_trial(self, version: dict) -> str:
        """
        Complete the trial and award XP.

        Args:
            version: Protocol version (full or quick)

        Returns:
            Closing message with XP award
        """
        # Award XP
        xp_amount = version.get("xp_award", 30)
        xp_source = version.get("xp_source", "evening_audit")
        skill = version.get("skill", "reflection")

        # Check for memento mori bonus
        if self.state.responses.get("memento_mori"):
            bonus = 25  # From protocol definition
            xp_amount += bonus
            logger.info(f"Memento Mori completed, +{bonus} bonus XP")

        # Save reflection to database
        self._save_reflection()

        # Award XP (fail-safe)
        self._award_xp(skill, xp_amount, xp_source)

        # Reset state
        self.state = TrialState()

        # Return closing with XP info
        closing = version.get("closing", "Reflection complete.")
        return f"{closing} Plus {xp_amount} reflection XP."

    def _save_reflection(self):
        """Save reflection responses to database."""
        try:
            from atlas.gamification import get_xp_service
            service = get_xp_service()

            # Map responses to database fields
            prosecution = self.state.responses.get("prosecution")
            judgment = self.state.responses.get("judgment")
            advocacy = self.state.responses.get("advocacy")
            memento_mori = bool(self.state.responses.get("memento_mori"))

            # Log reflection (this also awards XP through the service)
            service.log_reflection(
                prosecution=prosecution,
                judgment=judgment,
                advocacy=advocacy,
                memento_mori=memento_mori
            )

            logger.info("Reflection saved to database")

        except Exception as e:
            logger.error(f"Failed to save reflection: {e}")

    def _award_xp(self, skill: str, amount: int, source: str):
        """Award XP for completing reflection (fail-safe)."""
        try:
            from atlas.gamification.xp_service import award_xp_safe_async
            award_xp_safe_async(skill, amount, source)
            logger.info(f"Awarded {amount} XP to {skill}")
        except Exception as e:
            logger.warning(f"XP award failed (non-fatal): {e}")

    def cancel(self) -> str:
        """Cancel active trial without saving."""
        if not self.state.active:
            return "No active reflection to cancel."

        self.state = TrialState()
        return "Reflection cancelled. No XP awarded."

    def get_status(self) -> dict:
        """Get current trial status for UI/debugging."""
        if not self.state.active:
            return {"active": False}

        version_key = "quick" if self.state.is_quick else "full"
        version = self._protocol["versions"][version_key]
        phases = version["phases"]

        current_phase = phases[self.state.phase_index] if self.state.phase_index < len(phases) else None

        return {
            "active": True,
            "mode": "quick" if self.state.is_quick else "full",
            "phase_index": self.state.phase_index + 1,
            "total_phases": len(phases),
            "current_phase": current_phase["name"] if current_phase else "Complete",
            "responses_collected": len(self.state.responses),
        }


# Singleton instance for voice pipeline
_seneca_runner: Optional[SenecaRunner] = None


def get_seneca_runner() -> SenecaRunner:
    """Get singleton SenecaRunner instance."""
    global _seneca_runner
    if _seneca_runner is None:
        _seneca_runner = SenecaRunner()
    return _seneca_runner
