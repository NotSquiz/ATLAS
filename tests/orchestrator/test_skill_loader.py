"""Smoke tests for SkillLoader."""
import pytest
from pathlib import Path


class TestSkillLoader:
    """Test SkillLoader basic functionality."""
    
    def test_import(self):
        """Verify SkillLoader can be imported."""
        from atlas.orchestrator.skill_executor import SkillLoader
        loader = SkillLoader()
        assert loader is not None
    
    def test_list_skills(self):
        """Verify skills can be listed."""
        from atlas.orchestrator.skill_executor import SkillLoader
        loader = SkillLoader()
        skills = loader.list_skills()
        # Should find at least the activity skills
        assert isinstance(skills, list)
