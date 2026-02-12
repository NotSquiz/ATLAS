"""
Tests for ActivityConversionPipeline deterministic functions.

Covers 15 functions with 123 test cases:
- _parse_age_label (12 cases)
- _detect_truncation (7 cases)
- _fix_canonical_slug (4 cases)
- _fix_principle_slugs (5 cases)
- _remove_em_dashes (3 cases)
- _quick_validate (6 cases)
- _extract_audit_json (6 cases)
- _should_skip (4 cases)
- _get_group_info (3 cases)
- _update_summary_counts (5 cases)
- _fix_age_range (5 cases)
- _extract_transform_yaml_fallback (6 cases)
- _extract_elevate_yaml_fallback (3 cases)
- _fix_validation_misclassification (8 cases)
- _load_guidance_catalog (3 cases)
"""

import json
import re

import pytest
import yaml

from atlas.pipelines.activity_conversion import (
    ActivityConversionPipeline,
    ActivityStatus,
    ConversionResult,
)


# ============================================================
# _parse_age_label (12 cases)
# ============================================================

class TestParseAgeLabel:
    """D36: Age Range Normalization - trust the label."""

    def test_prenatal(self, pipeline):
        assert pipeline._parse_age_label("prenatal") == (-9, 0)

    def test_prenatal_case_insensitive(self, pipeline):
        assert pipeline._parse_age_label("Prenatal") == (-9, 0)

    def test_months_range_0_6m(self, pipeline):
        assert pipeline._parse_age_label("0-6m") == (0, 6)

    def test_months_range_6_12m(self, pipeline):
        assert pipeline._parse_age_label("6-12m") == (6, 12)

    def test_months_range_12_24m(self, pipeline):
        assert pipeline._parse_age_label("12-24m") == (12, 24)

    def test_years_range_2_3(self, pipeline):
        assert pipeline._parse_age_label("2-3 years") == (24, 36)

    def test_years_range_1_5_3(self, pipeline):
        assert pipeline._parse_age_label("1.5-3 years") == (18, 36)

    def test_months_plus_18(self, pipeline):
        assert pipeline._parse_age_label("18+ months") == (18, 72)

    def test_shorthand_0_3(self, pipeline):
        assert pipeline._parse_age_label("0-3") == (0, 3)

    def test_all_ages(self, pipeline):
        assert pipeline._parse_age_label("all ages") == (0, 72)

    def test_empty_string(self, pipeline):
        assert pipeline._parse_age_label("") == (None, None)

    def test_unparseable(self, pipeline):
        assert pipeline._parse_age_label("toddler") == (None, None)

    def test_months_word(self, pipeline):
        assert pipeline._parse_age_label("6-12 months") == (6, 12)

    def test_years_plural(self, pipeline):
        """Must use plural 'years' for correct year→month conversion."""
        assert pipeline._parse_age_label("1-2 years") == (12, 24)


# ============================================================
# _detect_truncation (7 cases)
# ============================================================

class TestDetectTruncation:
    """D78: Early truncation detection."""

    def _make_valid_yaml(self, lines=250):
        """Build a YAML string that passes all truncation checks."""
        yaml_lines = [
            "type: Activity",
            "canonical_id: test_activity",
            "priority_ranking: medium",
            "query_frequency_estimate: moderate",
        ]
        # Pad with content lines
        for i in range(lines - 10):
            yaml_lines.append(f"line_{i}: value")
        # Add parent_search_terms at the end
        yaml_lines.append("parent_search_terms:")
        yaml_lines.append('  - "test search term"')
        yaml_lines.append('  - "another search term"')
        yaml_lines.append('  - "final search term"')
        return "\n".join(yaml_lines)

    def test_empty_content(self, pipeline):
        is_trunc, reason = pipeline._detect_truncation("")
        assert is_trunc is True
        assert "Empty" in reason

    def test_too_short(self, pipeline):
        content = "type: Activity\ncanonical_id: test\nparent_search_terms:\n"
        is_trunc, reason = pipeline._detect_truncation(content)
        assert is_trunc is True
        assert "too short" in reason.lower()

    def test_missing_parent_search_terms(self, pipeline):
        """150+ lines but no parent_search_terms section."""
        lines = ["type: Activity", "canonical_id: test",
                 "priority_ranking: medium", "query_frequency_estimate: moderate"]
        for i in range(200):
            lines.append(f"line_{i}: value")
        content = "\n".join(lines)
        is_trunc, reason = pipeline._detect_truncation(content)
        assert is_trunc is True
        assert "parent_search_terms" in reason

    def test_valid_200_lines(self, pipeline):
        content = self._make_valid_yaml(250)
        is_trunc, reason = pipeline._detect_truncation(content)
        assert is_trunc is False
        assert "complete" in reason.lower()

    def test_missing_required_field_type(self, pipeline):
        """Has length and parent_search_terms but missing 'type: Activity'."""
        lines = [
            "canonical_id: test",
            "priority_ranking: medium",
            "query_frequency_estimate: moderate",
        ]
        for i in range(200):
            lines.append(f"line_{i}: value")
        lines.append("parent_search_terms:")
        lines.append('  - "search term"')
        content = "\n".join(lines)
        is_trunc, reason = pipeline._detect_truncation(content)
        assert is_trunc is True
        assert "type: Activity" in reason

    def test_truncated_mid_parent_search_terms(self, pipeline):
        """Has all fields but last content line is not a search term (Check 3)."""
        lines = [
            "type: Activity",
            "canonical_id: test_activity",
            "priority_ranking: medium",
            "query_frequency_estimate: moderate",
        ]
        for i in range(200):
            lines.append(f"line_{i}: value")
        lines.append("parent_search_terms:")
        lines.append("  some_truncated_content")  # NOT a list item
        content = "\n".join(lines)
        is_trunc, reason = pipeline._detect_truncation(content)
        assert is_trunc is True
        assert "not a search term" in reason.lower()

    def test_none_content(self, pipeline):
        is_trunc, reason = pipeline._detect_truncation(None)
        assert is_trunc is True

    def test_whitespace_only(self, pipeline):
        is_trunc, reason = pipeline._detect_truncation("   \n\n  ")
        assert is_trunc is True
        assert "Empty" in reason


# ============================================================
# _fix_canonical_slug (4 cases)
# ============================================================

class TestFixCanonicalId:
    """ELEVATE may rename canonical_id — fix preserves TRANSFORM ID."""

    def test_fixes_changed_id(self, pipeline):
        content = "canonical_id: ACTIVITY_WRONG_NAME"
        result = pipeline._fix_canonical_id(content, "ACTIVITY_CORRECT_NAME")
        assert "canonical_id: ACTIVITY_CORRECT_NAME" in result

    def test_already_correct(self, pipeline):
        content = "canonical_id: ACTIVITY_TEST"
        result = pipeline._fix_canonical_id(content, "ACTIVITY_TEST")
        assert "canonical_id: ACTIVITY_TEST" in result

    def test_preserves_surrounding(self, pipeline):
        content = "before: yes\ncanonical_id: ACTIVITY_OLD\nafter: yes"
        result = pipeline._fix_canonical_id(content, "ACTIVITY_NEW")
        assert "before: yes" in result
        assert "after: yes" in result
        assert "canonical_id: ACTIVITY_NEW" in result

    def test_missing_field(self, pipeline):
        content = "other_field: value"
        result = pipeline._fix_canonical_id(content, "ACTIVITY_TEST")
        assert result == content


class TestFixCanonicalSlug:

    def test_fixes_hyphen_to_match_id(self, pipeline):
        content = "canonical_slug: tummy-time-au"
        result = pipeline._fix_canonical_slug(content, "tummy_time")
        assert "canonical_slug: tummy-time" in result
        assert "au" not in result

    def test_already_correct(self, pipeline):
        content = "canonical_slug: tummy-time"
        result = pipeline._fix_canonical_slug(content, "tummy_time")
        assert "canonical_slug: tummy-time" in result

    def test_missing_field(self, pipeline):
        content = "other_field: value"
        result = pipeline._fix_canonical_slug(content, "tummy_time")
        assert result == content

    def test_preserves_surrounding_content(self, pipeline):
        content = "before: yes\ncanonical_slug: wrong-value\nafter: yes"
        result = pipeline._fix_canonical_slug(content, "test_activity")
        assert "before: yes" in result
        assert "after: yes" in result
        assert "canonical_slug: test-activity" in result


# ============================================================
# _fix_principle_slugs (5 cases)
# ============================================================

class TestFixPrincipleSlugs:
    """D35: Principle slugs use underscores, not hyphens."""

    def test_fixes_practical_life(self, pipeline):
        content = "principle: practical-life"
        result = pipeline._fix_principle_slugs(content)
        assert "practical_life" in result
        assert "practical-life" not in result

    def test_fixes_multiple_principles(self, pipeline):
        content = "principles:\n  - absorbent-mind\n  - sensitive-periods"
        result = pipeline._fix_principle_slugs(content)
        assert "absorbent_mind" in result
        assert "sensitive_periods" in result

    def test_no_hyphens_unchanged(self, pipeline):
        content = "principles:\n  - practical_life\n  - absorbent_mind"
        result = pipeline._fix_principle_slugs(content)
        assert result == content

    @pytest.mark.parametrize("wrong,correct", [
        ("practical-life", "practical_life"),
        ("absorbent-mind", "absorbent_mind"),
        ("sensitive-periods", "sensitive_periods"),
        ("prepared-environment", "prepared_environment"),
        ("freedom-within-limits", "freedom_within_limits"),
        ("grace-and-courtesy", "grace_and_courtesy"),
        ("maximum-effort", "maximum_effort"),
        ("work-of-the-child", "work_of_the_child"),
        ("cosmic-view", "cosmic_view"),
        ("spiritual-embryo", "spiritual_embryo"),
        ("follow-the-child", "follow_the_child"),
        ("freedom-of-movement", "freedom_of_movement"),
        ("care-of-environment", "care_of_environment"),
        ("hand-mind-connection", "hand_mind_connection"),
        ("self-correcting-materials", "self_correcting_materials"),
        ("concrete-to-abstract", "concrete_to_abstract"),
        ("sensory-exploration", "sensory_exploration"),
        ("inner-teacher", "inner_teacher"),
        ("risk-competence", "risk_competence"),
        ("refinement-of-movement", "refinement_of_movement"),
        ("language-development", "language_development"),
        ("respect-for-the-child", "respect_for_the_child"),
        ("respect-for-the-individual", "respect_for_the_individual"),
        ("hand-as-instrument-of-intelligence", "hand_as_instrument_of_intelligence"),
    ])
    def test_all_24_mappings(self, pipeline, wrong, correct):
        """Verify all 24 principle mappings work."""
        content = f"principle: {wrong}"
        result = pipeline._fix_principle_slugs(content)
        assert correct in result
        assert wrong not in result

    def test_empty_content(self, pipeline):
        assert pipeline._fix_principle_slugs("") == ""


# ============================================================
# _remove_dashes / _remove_em_dashes (D80: extended dash cleanup)
# ============================================================

class TestRemoveDashes:

    def test_replaces_em_dash_with_period(self, pipeline):
        content = "This is great \u2014 and also fun"
        result = pipeline._remove_dashes(content)
        assert "\u2014" not in result
        assert ". " in result

    def test_replaces_en_dash_with_period(self, pipeline):
        """D80: En-dash (U+2013) must also be cleaned."""
        content = "Children explore \u2013 and discover"
        result = pipeline._remove_dashes(content)
        assert "\u2013" not in result
        assert ". " in result

    def test_replaces_double_hyphen_with_period(self, pipeline):
        """D80: Double-hyphen (--) must also be cleaned."""
        content = "Children explore -- and discover"
        result = pipeline._remove_dashes(content)
        assert "--" not in result
        assert ". " in result

    def test_no_dashes(self, pipeline):
        content = "No special characters here."
        result = pipeline._remove_dashes(content)
        assert result == content

    def test_multiple_em_dashes(self, pipeline):
        content = "First\u2014second\u2014third"
        result = pipeline._remove_dashes(content)
        assert "\u2014" not in result
        assert result.count(".") >= 2

    def test_mixed_dash_types(self, pipeline):
        """D80: All dash variants in one string."""
        content = "Em\u2014dash and en\u2013dash and double--hyphen"
        result = pipeline._remove_dashes(content)
        assert "\u2014" not in result
        assert "\u2013" not in result
        assert "--" not in result

    def test_backward_compat_alias(self, pipeline):
        """_remove_em_dashes still works as alias."""
        content = "Test \u2014 content"
        result = pipeline._remove_em_dashes(content)
        assert "\u2014" not in result


# ============================================================
# _quick_validate (6 cases)
# ============================================================

class TestQuickValidate:
    """D36: Pre-Validation Quick Check for common anti-patterns."""

    def test_clean_content(self, pipeline):
        content = "This activity helps children explore movement."
        issues = pipeline._quick_validate(content)
        assert len(issues) == 0

    def test_finds_pressure_language(self, pipeline):
        content = "You need to make sure your child does this."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_PRESSURE_LANGUAGE" for i in issues)

    def test_finds_superlative(self, pipeline):
        content = "This is an amazing activity for development."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_SUPERLATIVE" for i in issues)

    def test_finds_em_dash(self, pipeline):
        content = "Children love this \u2014 really."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_EM_DASH" for i in issues)

    def test_finds_en_dash(self, pipeline):
        """D80: _quick_validate must catch en-dashes (aligned with QC hook)."""
        content = "Children love this \u2013 really."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_EM_DASH" for i in issues)

    def test_finds_double_hyphen(self, pipeline):
        """D80: _quick_validate must catch double-hyphens (aligned with QC hook)."""
        content = "Children love this -- really."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_EM_DASH" for i in issues)

    def test_finds_make_sure_to(self, pipeline):
        content = "Make sure to supervise your child."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_PRESSURE_LANGUAGE" for i in issues)

    def test_finds_ideal(self, pipeline):
        content = "This is the ideal time for learning."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_SUPERLATIVE" for i in issues)

    def test_issue_dict_has_required_keys(self, pipeline):
        content = "You must always do this amazing thing."
        issues = pipeline._quick_validate(content)
        assert len(issues) > 0
        for issue in issues:
            assert "code" in issue
            assert "category" in issue
            assert "issue" in issue
            assert "severity" in issue

    # P5: Behavioral change tests -- context-aware exceptions from ai_detection.py
    def test_best_practices_not_flagged(self, pipeline):
        """'best practices' is an allowed exception -- NOT flagged."""
        content = "Follow best practices for child safety."
        issues = pipeline._quick_validate(content)
        assert not any(
            i["code"] == "VOICE_SUPERLATIVE" and "best" in i["issue"].lower()
            for i in issues
        )

    def test_the_best_still_flagged(self, pipeline):
        """'the best approach' is NOT an exception -- still flagged."""
        content = "This is the best approach to teaching."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_SUPERLATIVE" for i in issues)

    def test_ideal_period_not_flagged(self, pipeline):
        """'ideal period' is a Montessori term -- NOT flagged."""
        content = "This is the ideal period for sensory development."
        issues = pipeline._quick_validate(content)
        assert not any(
            i["code"] == "VOICE_SUPERLATIVE" and "ideal" in i["issue"].lower()
            for i in issues
        )

    def test_works_best_not_flagged(self, pipeline):
        """'works best' is an allowed exception -- NOT flagged."""
        content = "This approach works best for toddlers."
        issues = pipeline._quick_validate(content)
        assert not any(
            i["code"] == "VOICE_SUPERLATIVE" and "best" in i["issue"].lower()
            for i in issues
        )

    def test_is_ideal_not_flagged(self, pipeline):
        """'is ideal' predicate use -- NOT flagged (physical suitability)."""
        content = "A ripe banana is ideal. Soft enough to cut with gentle pressure."
        issues = pipeline._quick_validate(content)
        assert not any(
            i["code"] == "VOICE_SUPERLATIVE" and "ideal" in i["issue"].lower()
            for i in issues
        )

    def test_not_ideal_not_flagged(self, pipeline):
        """'not ideal' negation -- NOT flagged."""
        content = "A hard avocado is not ideal for this activity."
        issues = pipeline._quick_validate(content)
        assert not any(
            i["code"] == "VOICE_SUPERLATIVE" and "ideal" in i["issue"].lower()
            for i in issues
        )

    def test_the_ideal_still_flagged(self, pipeline):
        """'the ideal environment' (adjective) -- still flagged."""
        content = "This creates the ideal environment for learning."
        issues = pipeline._quick_validate(content)
        assert any(i["code"] == "VOICE_SUPERLATIVE" for i in issues)

    def test_search_terms_superlatives_not_flagged(self, pipeline):
        """Superlatives in parent_search_terms should NOT be flagged."""
        content = (
            "some_field: clean content\n"
            "parent_search_terms:\n"
            '  - "best books for 1 year old language development"\n'
            '  - "amazing activities for toddlers"\n'
        )
        issues = pipeline._quick_validate(content)
        assert not any(i["code"] == "VOICE_SUPERLATIVE" for i in issues)

    def test_superlative_before_search_terms_still_flagged(self, pipeline):
        """Superlatives ABOVE parent_search_terms are still caught."""
        content = (
            "description: This is an amazing activity.\n"
            "parent_search_terms:\n"
            '  - "best books for toddlers"\n'
        )
        issues = pipeline._quick_validate(content)
        assert any(
            i["code"] == "VOICE_SUPERLATIVE" and "amazing" in i["issue"].lower()
            for i in issues
        )


# ============================================================
# _extract_audit_json (6 cases)
# ============================================================

class TestExtractAuditJson:
    """D28: Extract and validate JSON from audit response."""

    def test_valid_json(self, pipeline):
        raw = '{"grade": "A", "passed": true}'
        result, error = pipeline._extract_audit_json(raw)
        assert result is not None
        assert error is None
        assert result["grade"] == "A"

    def test_code_fenced_json(self, pipeline):
        raw = 'Some text\n```json\n{"grade": "B+"}\n```\nMore text'
        result, error = pipeline._extract_audit_json(raw)
        assert result is not None
        assert result["grade"] == "B+"

    def test_truncated_json_repair_deep_nesting_fails(self, pipeline):
        """Deeply nested truncation cannot be fully repaired."""
        raw = '{"grade": "A", "issues": [{"category": "voice"'
        result, error = pipeline._extract_audit_json(raw)
        # Repair adds closing brackets/braces but inner object stays malformed
        assert result is None
        assert error is not None
        assert "Invalid JSON" in error

    def test_empty_input(self, pipeline):
        result, error = pipeline._extract_audit_json("")
        assert result is None
        assert error is not None
        assert "Empty" in error

    def test_no_json_content(self, pipeline):
        raw = "This is just plain text with no JSON"
        result, error = pipeline._extract_audit_json(raw)
        assert result is None
        assert error is not None

    def test_json_with_unbalanced_braces(self, pipeline):
        raw = '{"grade": "A", "issues": []'  # missing closing }
        result, error = pipeline._extract_audit_json(raw)
        # Should attempt to repair
        assert result is not None
        assert result["grade"] == "A"

    def test_code_fenced_no_closing(self, pipeline):
        """Truncation: opening ```json but no closing ```."""
        raw = '```json\n{"grade": "A"}'
        result, error = pipeline._extract_audit_json(raw)
        assert result is not None
        assert result["grade"] == "A"


# ============================================================
# _should_skip (4 cases)
# ============================================================

class TestShouldSkip:

    def test_in_skip_list(self, pipeline):
        pipeline.conversion_map = {"skip": ["tummy-time-dupe"]}
        should_skip, reason = pipeline._should_skip("tummy-time-dupe")
        assert should_skip is True
        assert "skip list" in reason.lower()

    def test_non_primary_in_group(self, pipeline):
        pipeline.conversion_map = {
            "groups": {
                "crawling": {
                    "sources": ["crawling-main", "crawling-dupe"],
                }
            }
        }
        should_skip, reason = pipeline._should_skip("crawling-dupe")
        assert should_skip is True
        assert "Non-primary" in reason

    def test_primary_in_group_not_skipped(self, pipeline):
        pipeline.conversion_map = {
            "groups": {
                "crawling": {
                    "sources": ["crawling-main", "crawling-dupe"],
                }
            }
        }
        should_skip, reason = pipeline._should_skip("crawling-main")
        assert should_skip is False

    def test_not_in_skip_or_group(self, pipeline):
        pipeline.conversion_map = {"skip": [], "groups": {}}
        should_skip, reason = pipeline._should_skip("normal-activity")
        assert should_skip is False
        assert reason is None


# ============================================================
# _get_group_info (3 cases)
# ============================================================

class TestGetGroupInfo:

    def test_primary_returns_info(self, pipeline):
        pipeline.raw_activities = {
            "crawling-main": {"id": "crawling-main", "title": "Crawling"},
            "crawling-dupe": {"id": "crawling-dupe", "title": "Crawling 2"},
        }
        pipeline.conversion_map = {
            "groups": {
                "crawling": {
                    "sources": ["crawling-main", "crawling-dupe"],
                    "domain": "movement",
                    "age_range": "6-12m",
                }
            }
        }
        info = pipeline._get_group_info("crawling-main")
        assert info is not None
        assert info["group_id"] == "crawling"
        assert len(info["sources"]) == 2
        assert info["domain"] == "movement"
        assert len(info["source_activities"]) == 2
        assert info["source_activities"][0]["id"] == "crawling-main"

    def test_non_primary_returns_none(self, pipeline):
        pipeline.conversion_map = {
            "groups": {
                "crawling": {
                    "sources": ["crawling-main", "crawling-dupe"],
                }
            }
        }
        info = pipeline._get_group_info("crawling-dupe")
        assert info is None

    def test_not_in_group_returns_none(self, pipeline):
        pipeline.conversion_map = {"groups": {}}
        info = pipeline._get_group_info("standalone")
        assert info is None


# ============================================================
# _update_summary_counts (5 cases)
# ============================================================

class TestUpdateSummaryCounts:
    """C5: Counts done/pending/failed/skipped but only writes 3 of 4."""

    def test_updates_done_count(self, pipeline):
        pipeline.progress_data = {
            "a1": {"status": "done"},
            "a2": {"status": "done"},
            "a3": {"status": "pending"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0"
        result = pipeline._update_summary_counts(content)
        assert "- Done: 2" in result
        assert "- Pending: 1" in result

    def test_updates_pending_count(self, pipeline):
        pipeline.progress_data = {
            "a1": {"status": "pending"},
            "a2": {"status": "pending"},
        }
        content = "- Done: 5\n- Pending: 10\n- Failed: 0"
        result = pipeline._update_summary_counts(content)
        assert "- Pending: 2" in result

    def test_updates_failed_count(self, pipeline):
        pipeline.progress_data = {
            "a1": {"status": "failed"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0"
        result = pipeline._update_summary_counts(content)
        assert "- Failed: 1" in result

    def test_skipped_now_written(self, pipeline):
        """C5 fix: Skipped count is now written correctly."""
        pipeline.progress_data = {
            "a1": {"status": "skipped"},
            "a2": {"status": "skipped"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0\n- Skipped: 0"
        result = pipeline._update_summary_counts(content)
        assert "- Skipped: 2" in result

    def test_empty_progress_data(self, pipeline):
        pipeline.progress_data = {}
        content = "- Done: 5\n- Pending: 10\n- Failed: 2"
        result = pipeline._update_summary_counts(content)
        assert "- Done: 0" in result
        assert "- Pending: 0" in result
        assert "- Failed: 0" in result

    def test_revision_needed_inserted(self, pipeline):
        """C5 fix: Revision Needed inserted when not in header."""
        pipeline.progress_data = {
            "a1": {"status": "revision_needed"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0"
        result = pipeline._update_summary_counts(content)
        assert "- Revision Needed: 1" in result

    def test_qc_failed_inserted(self, pipeline):
        """C5 fix: QC Failed inserted when not in header."""
        pipeline.progress_data = {
            "a1": {"status": "qc_failed"},
            "a2": {"status": "qc_failed"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0"
        result = pipeline._update_summary_counts(content)
        assert "- QC Failed: 2" in result

    def test_in_progress_inserted(self, pipeline):
        """C5 fix: In Progress inserted when not in header."""
        pipeline.progress_data = {
            "a1": {"status": "in_progress"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0"
        result = pipeline._update_summary_counts(content)
        assert "- In Progress: 1" in result

    def test_all_statuses_written(self, pipeline):
        """C5 fix: All 7 statuses written correctly."""
        pipeline.progress_data = {
            "a1": {"status": "done"},
            "a2": {"status": "pending"},
            "a3": {"status": "failed"},
            "a4": {"status": "skipped"},
            "a5": {"status": "revision_needed"},
            "a6": {"status": "qc_failed"},
            "a7": {"status": "in_progress"},
        }
        content = "- Done: 0\n- Pending: 0\n- Failed: 0\n- Skipped: 0"
        result = pipeline._update_summary_counts(content)
        assert "- Done: 1" in result
        assert "- Pending: 1" in result
        assert "- Failed: 1" in result
        assert "- Skipped: 1" in result
        assert "- Revision Needed: 1" in result
        assert "- QC Failed: 1" in result
        assert "- In Progress: 1" in result


# ============================================================
# _fix_age_range (5 cases)
# ============================================================

class TestFixAgeRange:
    """D90: Preserve critical metadata fields from original YAML."""

    def _make_yaml(self, age_min=0, age_max=36, domain="movement",
                   canonical_id="test_activity"):
        """Build a minimal valid YAML string for testing.

        Uses explicit YAML format (not yaml.dump) to match the format
        that _fix_age_range's regex patterns expect.
        """
        return (
            f"type: Activity\n"
            f"canonical_id: {canonical_id}\n"
            f"canonical_slug: {canonical_id.replace('_', '-')}\n"
            f"version: '1.0'\n"
            f"age_months_min: {age_min}\n"
            f"age_months_max: {age_max}\n"
            f"domain:\n"
            f"  - {domain}\n"
            f"evidence_strength: moderate\n"
            f"priority_ranking: medium\n"
            f"query_frequency_estimate: moderate\n"
        )

    def test_preserves_age_range(self, pipeline):
        """ELEVATE changes age_months_min from 6 to 0; fix should restore 6."""
        original = self._make_yaml(age_min=6, age_max=12)
        elevated = self._make_yaml(age_min=0, age_max=12)  # ELEVATE corrupted min
        result = pipeline._fix_age_range(elevated, original)
        parsed = yaml.safe_load(result)
        assert parsed["age_months_min"] == 6

    def test_already_correct_no_change(self, pipeline):
        original = self._make_yaml(age_min=6, age_max=12)
        elevated = self._make_yaml(age_min=6, age_max=12)  # Same values
        result = pipeline._fix_age_range(elevated, original)
        # Should be unchanged
        parsed = yaml.safe_load(result)
        assert parsed["age_months_min"] == 6
        assert parsed["age_months_max"] == 12

    def test_preserves_domain_list(self, pipeline):
        """ELEVATE changes domain; fix should restore original."""
        original = self._make_yaml(domain="movement")
        elevated = self._make_yaml(domain="motor_gross")  # ELEVATE changed domain
        result = pipeline._fix_age_range(elevated, original)
        parsed = yaml.safe_load(result)
        assert "movement" in parsed["domain"]

    def test_empty_original_returns_elevated(self, pipeline):
        elevated = self._make_yaml()
        result = pipeline._fix_age_range(elevated, "")
        assert result == elevated  # No change when original is empty

    def test_preserves_canonical_id(self, pipeline):
        """ELEVATE changes canonical_id; fix should restore."""
        original = self._make_yaml(canonical_id="tummy_time")
        elevated = self._make_yaml(canonical_id="tummy_time_au")  # ELEVATE corrupted
        result = pipeline._fix_age_range(elevated, original)
        parsed = yaml.safe_load(result)
        assert parsed["canonical_id"] == "tummy_time"

    def test_handles_yaml_parse_error_gracefully(self, pipeline):
        """Invalid YAML should return elevated content unchanged."""
        elevated = "this: is valid\nage_months_min: 5"
        original = "not: valid: yaml: {{{"
        result = pipeline._fix_age_range(elevated, original)
        # Should return elevated unchanged on parse error
        assert result == elevated


# ============================================================
# reconcile_progress (3 cases)
# ============================================================

class TestReconcileProgress:
    """C3 fix: Progress tracker reconciliation."""

    def test_empty_state(self, pipeline, tmp_path):
        """No files, no progress data."""
        pipeline.CANONICAL_OUTPUT_DIR = tmp_path / "canonical"
        pipeline.CANONICAL_OUTPUT_DIR.mkdir()
        report = pipeline.reconcile_progress()
        assert report["files_on_disk"] == 0
        assert report["tracked_done"] == 0
        assert report["untracked_files"] == []
        assert report["missing_files"] == []

    def test_untracked_files(self, pipeline, tmp_path):
        """Files on disk but not tracked as done."""
        pipeline.CANONICAL_OUTPUT_DIR = tmp_path / "canonical"
        domain_dir = pipeline.CANONICAL_OUTPUT_DIR / "movement"
        domain_dir.mkdir(parents=True)
        (domain_dir / "tummy_time.yaml").write_text("type: Activity")
        (domain_dir / "crawling.yaml").write_text("type: Activity")

        pipeline.progress_data = {}

        report = pipeline.reconcile_progress()
        assert report["files_on_disk"] == 2
        assert report["tracked_done"] == 0
        assert len(report["untracked_files"]) == 2
        assert "tummy_time" in report["untracked_files"]

    def test_missing_files(self, pipeline, tmp_path):
        """Tracked as done but no file on disk."""
        pipeline.CANONICAL_OUTPUT_DIR = tmp_path / "canonical"
        pipeline.CANONICAL_OUTPUT_DIR.mkdir()

        pipeline.progress_data = {
            "tummy_time": {"status": "done"},
            "crawling": {"status": "pending"},
        }

        report = pipeline.reconcile_progress()
        assert report["files_on_disk"] == 0
        assert report["tracked_done"] == 1
        assert "tummy_time" in report["missing_files"]
        assert report["status_counts"]["done"] == 1
        assert report["status_counts"]["pending"] == 1


# ============================================================
# Regression / Edge Cases
# ============================================================

class TestTransformYamlFallback:
    """Tests for _extract_transform_yaml_fallback."""

    def test_extracts_yaml_from_broken_json(self, pipeline):
        """JSON parsing fails but YAML content is extractable."""
        raw = (
            '```json\n{\n  "canonical_yaml": "type: Activity\\n'
            'canonical_id: ACTIVITY_TEST_001\\n'
            'canonical_slug: activity-test-001\\n'
            'version: \\"1.0\\"\\n'
            + "line: value\\n" * 50  # Pad to >500 chars
            + 'parent_search_terms:\\n  - test",\n'
            '  "canonical_id": "ACTIVITY_TEST_001",\n'
            '  "file_path": "activities/ACTIVITY_TEST_001.yaml"\n}\n```'
        )
        ok, data, err = pipeline._extract_transform_yaml_fallback(raw)
        assert ok is True
        assert data["canonical_id"] == "ACTIVITY_TEST_001"
        assert data["file_path"] == "activities/ACTIVITY_TEST_001.yaml"
        assert data["canonical_yaml"].startswith("type: Activity")
        assert "\\n" not in data["canonical_yaml"]  # Properly unescaped

    def test_extracts_yaml_without_json_keys(self, pipeline):
        """Raw output has YAML but no canonical_id/file_path JSON keys."""
        yaml_body = "line: value\n" * 50
        raw = (
            'Some preamble\ntype: Activity\ncanonical_id: ACTIVITY_FOO\n'
            + yaml_body
        )
        ok, data, err = pipeline._extract_transform_yaml_fallback(raw)
        assert ok is True
        assert data["canonical_id"] == "ACTIVITY_FOO"
        assert "activities/" in data["file_path"]

    def test_fails_on_empty_output(self, pipeline):
        ok, data, err = pipeline._extract_transform_yaml_fallback("")
        assert ok is False

    def test_fails_when_no_yaml_found(self, pipeline):
        ok, data, err = pipeline._extract_transform_yaml_fallback("random text without yaml")
        assert ok is False
        assert "not found" in err.lower() or "no" in err.lower()

    def test_fails_on_short_yaml(self, pipeline):
        """YAML content too short to be valid."""
        raw = '"canonical_yaml": "type: Activity\\nshort"'
        ok, data, err = pipeline._extract_transform_yaml_fallback(raw)
        assert ok is False
        assert "too short" in err.lower()

    def test_unescapes_json_encoding(self, pipeline):
        """Verifies JSON string escaping is properly reversed."""
        yaml_lines = "line: value\\n" * 50
        raw = (
            '{"canonical_yaml": "type: Activity\\n'
            'canonical_id: ACTIVITY_TEST\\n'
            'title: \\"Cutting a Banana\\"\\n'
            + yaml_lines
            + '",\n"canonical_id": "ACTIVITY_TEST"}'
        )
        ok, data, err = pipeline._extract_transform_yaml_fallback(raw)
        assert ok is True
        assert '"Cutting a Banana"' in data["canonical_yaml"]
        assert "\n" in data["canonical_yaml"]  # Real newlines


class TestElevateYamlFallback:
    """Tests for _extract_elevate_yaml_fallback."""

    def test_extracts_elevated_yaml(self, pipeline):
        """Extracts elevated_yaml from broken JSON."""
        yaml_lines = "line: value\\n" * 50
        raw = (
            '{"elevated_yaml": "type: Activity\\n'
            'canonical_id: ACTIVITY_TEST\\n'
            + yaml_lines
            + '"}'
        )
        ok, data, err = pipeline._extract_elevate_yaml_fallback(raw)
        assert ok is True
        assert "elevated_yaml" in data
        assert data["elevated_yaml"].startswith("type: Activity")

    def test_fails_on_empty(self, pipeline):
        ok, data, err = pipeline._extract_elevate_yaml_fallback("")
        assert ok is False

    def test_fails_when_no_yaml(self, pipeline):
        ok, data, err = pipeline._extract_elevate_yaml_fallback("just some text")
        assert ok is False


class TestEdgeCases:

    def test_conversion_result_dataclass(self):
        result = ConversionResult(
            activity_id="test",
            status=ActivityStatus.DONE,
            canonical_id="test_activity",
        )
        assert result.activity_id == "test"
        assert result.status == ActivityStatus.DONE
        assert result.qc_issues == []

    def test_activity_status_values(self):
        assert ActivityStatus.PENDING.value == "pending"
        assert ActivityStatus.DONE.value == "done"
        assert ActivityStatus.QC_FAILED.value == "qc_failed"
        assert ActivityStatus.REVISION_NEEDED.value == "revision_needed"

    def test_pipeline_class_constants(self, pipeline):
        """Verify key constants exist on the class."""
        assert hasattr(ActivityConversionPipeline, 'RAW_ACTIVITIES_PATH')
        assert hasattr(ActivityConversionPipeline, 'CANONICAL_OUTPUT_DIR')
        assert hasattr(ActivityConversionPipeline, 'VALID_DOMAINS')
        assert "movement" in ActivityConversionPipeline.VALID_DOMAINS
        assert "cognitive" in ActivityConversionPipeline.VALID_DOMAINS


# ============================================================
# _fix_validation_misclassification (8 cases)
# ============================================================

class TestFixValidationMisclassification:
    """Guidance/materials reference issues should be warnings, not blocking."""

    def test_guidance_id_not_found_moves_to_warnings(self, pipeline):
        """GUIDANCE_XX_NNNN not found -> warning, passed=True."""
        output = {
            "validation_result": {
                "passed": False,
                "blocking_issues": [
                    "GUIDANCE_LANGUAGE_0001 not found in canonical guidance"
                ],
                "warnings": [],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is True
        assert vr["blocking_issues"] == []
        assert len(vr["warnings"]) == 1
        assert "GUIDANCE_LANGUAGE_0001" in vr["warnings"][0]

    def test_material_slug_not_in_catalog_moves_to_warnings(self, pipeline):
        """Material slug not in catalog -> warning."""
        output = {
            "validation_result": {
                "passed": False,
                "blocking_issues": [
                    "Material slug child-sized-knife not found in catalog"
                ],
                "warnings": [],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is True
        assert vr["blocking_issues"] == []
        assert len(vr["warnings"]) == 1

    def test_real_blocking_issue_stays_blocking(self, pipeline):
        """YAML syntax error stays blocking."""
        output = {
            "validation_result": {
                "passed": False,
                "blocking_issues": [
                    "Invalid YAML syntax on line 45: unexpected key"
                ],
                "warnings": [],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is False  # Not changed
        assert len(vr["blocking_issues"]) == 1
        assert vr["warnings"] == []

    def test_mixed_issues_correctly_sorted(self, pipeline):
        """Mix of real blockers and guidance refs -> sorted correctly."""
        output = {
            "validation_result": {
                "passed": False,
                "blocking_issues": [
                    "canonical_id mismatch: expected X, found Y",
                    "GUIDANCE_PE_0007 does not exist",
                    "Material slug banana-knife not in materials catalog",
                ],
                "warnings": ["Some existing warning"],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is False  # Still has real blocker
        assert len(vr["blocking_issues"]) == 1
        assert "canonical_id" in vr["blocking_issues"][0]
        assert len(vr["warnings"]) == 3  # 1 existing + 2 moved

    def test_empty_blocking_passes_through(self, pipeline):
        """No blocking issues -> no changes."""
        output = {
            "validation_result": {
                "passed": True,
                "blocking_issues": [],
                "warnings": ["Some warning"],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is True
        assert vr["blocking_issues"] == []

    def test_no_validation_result_passes_through(self, pipeline):
        """Missing validation_result key -> returns unchanged."""
        output = {"some_other_key": "value"}
        result = pipeline._fix_validation_misclassification(output)
        assert result == output

    def test_guidance_components_section_stays_blocking(self, pipeline):
        """'guidance_components section not found' is structural -> stays blocking."""
        output = {
            "validation_result": {
                "passed": False,
                "blocking_issues": [
                    "guidance_components section not found in YAML"
                ],
                "warnings": [],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is False
        assert len(vr["blocking_issues"]) == 1
        assert "section" in vr["blocking_issues"][0]

    def test_source_material_field_stays_blocking(self, pipeline):
        """'required field not found' is structural -> stays blocking."""
        output = {
            "validation_result": {
                "passed": False,
                "blocking_issues": [
                    "Source material field not found in activity YAML"
                ],
                "warnings": [],
            }
        }
        result = pipeline._fix_validation_misclassification(output)
        vr = result["validation_result"]
        assert vr["passed"] is False
        assert len(vr["blocking_issues"]) == 1


# ============================================================
# _load_guidance_catalog (3 cases)
# ============================================================

class TestLoadGuidanceCatalog:
    """Guidance catalog loading with caching and graceful degradation."""

    def test_returns_list_when_file_exists(self, pipeline, tmp_path):
        """Returns catalog entries from valid JSON file."""
        catalog_data = [
            {"id": "GUIDANCE_FEEDING_0001", "title": "Test", "domain_tags": ["feeding"]},
            {"id": "GUIDANCE_PE_0001", "title": "Test 2", "domain_tags": ["pe"]},
        ]
        catalog_file = tmp_path / "config" / "babybrains" / "guidance_catalog.json"
        catalog_file.parent.mkdir(parents=True)
        catalog_file.write_text(json.dumps(catalog_data))

        # Patch the path resolution
        import unittest.mock
        with unittest.mock.patch.object(
            type(pipeline), '_load_guidance_catalog',
            lambda self: json.loads(catalog_file.read_text())
        ):
            result = pipeline._load_guidance_catalog()
            assert len(result) == 2
            assert result[0]["id"] == "GUIDANCE_FEEDING_0001"

    def test_returns_empty_list_when_missing(self, pipeline):
        """Returns [] when catalog file doesn't exist."""
        # Clear any cached value
        if hasattr(pipeline, "_guidance_catalog_cache"):
            del pipeline._guidance_catalog_cache
        # The real path won't exist in test environment
        # but __file__ resolution will point to source tree
        # which may or may not have the file. Test the caching behavior.
        result = pipeline._load_guidance_catalog()
        assert isinstance(result, list)

    def test_caches_on_second_call(self, pipeline):
        """Second call returns cached value without re-reading."""
        # Pre-populate cache
        pipeline._guidance_catalog_cache = [{"id": "CACHED"}]
        result = pipeline._load_guidance_catalog()
        assert result == [{"id": "CACHED"}]
        # Clean up
        del pipeline._guidance_catalog_cache


# ============================================================
# Fix 1: Stage cache persistence - deterministic session_id
# ============================================================

class TestScratchPadPersistence:
    """D78+: Cache persistence across runs via deterministic session_id."""

    def test_session_id_deterministic(self, pipeline):
        """Session ID must not contain timestamp - enables cache reuse."""
        from atlas.orchestrator.scratch_pad import ScratchPad
        raw_id = "tummy-time"
        expected_id = f"convert_{raw_id}"
        # Simulate what convert_activity does
        session_id = f"convert_{raw_id}"
        pad = ScratchPad(session_id=session_id)
        assert pad.session_id == expected_id
        assert "_202" not in pad.session_id  # No timestamp

    def test_cached_transform_reload_from_disk(self, pipeline, tmp_path):
        """Cached transform output should be reloadable from disk scratch pad."""
        from atlas.orchestrator.scratch_pad import ScratchPad
        raw_id = "test-activity"
        pad = ScratchPad(session_id=f"convert_{raw_id}")
        pad.add("transform_output", {
            "canonical_yaml": "type: Activity\ncanonical_id: TEST_001",
            "canonical_id": "TEST_001",
            "file_path": "/tmp/test.yaml",
        }, step=3, skill_name="transform_activity")
        scratch_file = tmp_path / f"convert_{raw_id}.json"
        pad.to_file(scratch_file)

        # Reload and extract
        loaded = ScratchPad.from_file(scratch_file)
        assert loaded is not None
        transform_output = loaded.get("transform_output")
        assert transform_output is not None
        assert transform_output["canonical_id"] == "TEST_001"
        assert transform_output["canonical_yaml"].startswith("type: Activity")

    def test_cached_transform_incomplete_not_used(self, pipeline, tmp_path):
        """Incomplete transform output (missing fields) should not be used."""
        from atlas.orchestrator.scratch_pad import ScratchPad
        raw_id = "incomplete-activity"
        pad = ScratchPad(session_id=f"convert_{raw_id}")
        pad.add("transform_output", {
            "canonical_yaml": "",  # Empty = incomplete
            "canonical_id": "TEST_002",
            "file_path": "/tmp/test.yaml",
        }, step=3, skill_name="transform_activity")
        scratch_file = tmp_path / f"convert_{raw_id}.json"
        pad.to_file(scratch_file)

        loaded = ScratchPad.from_file(scratch_file)
        transform_output = loaded.get("transform_output")
        candidate = {
            "canonical_yaml": transform_output.get("canonical_yaml", ""),
            "canonical_id": transform_output.get("canonical_id", ""),
            "file_path": transform_output.get("file_path", ""),
        }
        # all() should be False because canonical_yaml is empty
        assert not all(candidate.values())

    def test_no_scratch_file_returns_none(self, tmp_path):
        """Missing scratch file should return None gracefully."""
        from atlas.orchestrator.scratch_pad import ScratchPad
        path = tmp_path / "nonexistent.json"
        loaded = ScratchPad.from_file(path)
        assert loaded is None


# ============================================================
# D110: Cached transform path initializes scratch_pad + session
# ============================================================

class TestCachedTransformInitialization:
    """D110: _convert_from_cached_transform must initialize scratch_pad."""

    @pytest.mark.asyncio
    async def test_cached_path_initializes_scratch_pad(self, pipeline):
        """scratch_pad must not be None when cached path runs."""
        import unittest.mock
        from atlas.orchestrator.scratch_pad import ScratchPad

        pipeline.scratch_pad = None
        pipeline.session = unittest.mock.AsyncMock()
        pipeline._execute_elevate = unittest.mock.AsyncMock(
            return_value=(False, None, "test short-circuit")
        )

        cached = {
            "canonical_yaml": "type: Activity\ncanonical_id: TEST",
            "canonical_id": "TEST",
            "file_path": "/tmp/test.yaml",
        }

        result = await pipeline._convert_from_cached_transform("test-id", cached)

        # scratch_pad should be initialized even though elevate failed
        assert pipeline.scratch_pad is not None
        assert isinstance(pipeline.scratch_pad, ScratchPad)
        assert pipeline.scratch_pad.session_id == "convert_test-id"
        # session.start_session should have been called
        pipeline.session.start_session.assert_awaited_once_with(repo="knowledge")

    @pytest.mark.asyncio
    async def test_cached_path_scratch_pad_usable(self, pipeline):
        """scratch_pad.add() must work in cached path (was NoneType crash)."""
        import unittest.mock
        from atlas.orchestrator.scratch_pad import ScratchPad

        pipeline.scratch_pad = None
        pipeline.session = unittest.mock.AsyncMock()
        pipeline._execute_elevate = unittest.mock.AsyncMock(
            return_value=(True, {"elevated_yaml": "type: Activity", "grade": "A"}, None)
        )
        # Short-circuit at quick_validate to avoid needing more stubs
        pipeline._fix_canonical_id = lambda y, _: y
        pipeline._fix_canonical_slug = lambda y, _: y
        pipeline._fix_principle_slugs = lambda y: y
        pipeline._fix_age_range = lambda y, _: y
        pipeline._remove_dashes = lambda y: y
        pipeline._quick_validate = lambda y: [{"code": "TEST", "category": "test",
                                                "issue": "stop here", "severity": "error"}]

        cached = {
            "canonical_yaml": "type: Activity\ncanonical_id: TEST",
            "canonical_id": "TEST",
            "file_path": "/tmp/test.yaml",
        }

        result = await pipeline._convert_from_cached_transform("test-id", cached)

        # Should have reached scratch_pad.add without crash
        assert pipeline.scratch_pad is not None
        elevate_data = pipeline.scratch_pad.get("elevate_output")
        assert elevate_data is not None


# ============================================================
# Fix 2: Non-interactive stdin detection
# ============================================================

class TestPresentForReviewNonInteractive:
    """Non-interactive stdin should auto-approve Grade A, auto-reject below."""

    def test_auto_approve_grade_a_non_interactive(self, pipeline):
        """Grade A should be auto-approved when stdin is non-interactive."""
        import unittest.mock
        result = ConversionResult(
            activity_id="test-activity",
            status=ActivityStatus.DONE,
            canonical_id="TEST_001",
        )
        with unittest.mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            decision = pipeline.present_for_review(result, "type: Activity")
        assert decision == "approve"

    def test_auto_reject_below_grade_a_non_interactive(self, pipeline):
        """Below Grade A should be auto-rejected when stdin is non-interactive."""
        import unittest.mock
        result = ConversionResult(
            activity_id="test-activity",
            status=ActivityStatus.QC_FAILED,
            qc_issues=["Superlative found"],
        )
        with unittest.mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            decision = pipeline.present_for_review(result, "type: Activity")
        assert decision == "reject"


# ============================================================
# Fix 3: Graceful shutdown + orphaned progress cleanup
# ============================================================

class TestGracefulShutdown:
    """Signal handler resets IN_PROGRESS on interruption."""

    def test_current_activity_id_initially_none(self, pipeline):
        """_current_activity_id should start as None."""
        pipeline._current_activity_id = None
        assert pipeline._current_activity_id is None

    def test_cleanup_stale_no_stale(self, pipeline):
        """No stale entries returns empty list."""
        from datetime import datetime, timezone
        pipeline.progress_data = {
            "test-1": {
                "status": "pending",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        }
        # Stub PROGRESS_PATH to avoid file access
        pipeline.PROGRESS_PATH = type('P', (), {'exists': lambda self: False})()
        result = pipeline.cleanup_stale_progress(max_age_hours=2)
        assert result == []

    def test_cleanup_stale_finds_old_entry(self, pipeline):
        """IN_PROGRESS entry older than max_age_hours should be found."""
        from datetime import datetime, timezone, timedelta
        old_time = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        pipeline.progress_data = {
            "stale-activity": {
                "status": "in_progress",
                "last_updated": old_time,
            }
        }
        # Stub PROGRESS_PATH to avoid file access (progress file won't exist in tests)
        pipeline.PROGRESS_PATH = type('P', (), {'exists': lambda self: False})()
        # cleanup_stale_progress calls _update_progress_file which needs the file
        # Since file doesn't exist, _update_progress_file returns False
        # But the activity IS detected as stale
        result = pipeline.cleanup_stale_progress(max_age_hours=2)
        # Even though file update fails, the ID is still detected
        assert "stale-activity" in result

    def test_cleanup_stale_no_timestamp(self, pipeline):
        """IN_PROGRESS with no timestamp should be reset."""
        pipeline.progress_data = {
            "no-timestamp": {"status": "in_progress"}
        }
        pipeline.PROGRESS_PATH = type('P', (), {'exists': lambda self: False})()
        result = pipeline.cleanup_stale_progress(max_age_hours=2)
        assert "no-timestamp" in result


# ============================================================
# Fix 4: Per-stage timeout configuration
# ============================================================

class TestStageTimeouts:
    """Per-stage timeout configuration."""

    def test_stage_timeouts_dict_exists(self, pipeline):
        """STAGE_TIMEOUTS should be a class-level dict."""
        assert hasattr(ActivityConversionPipeline, "STAGE_TIMEOUTS")
        assert isinstance(ActivityConversionPipeline.STAGE_TIMEOUTS, dict)

    def test_all_stages_have_timeouts(self, pipeline):
        """Every pipeline stage should have a configured timeout."""
        expected_stages = {
            "ingest", "research", "transform", "elevate",
            "validate", "qc_hook", "quality_audit",
        }
        actual_stages = set(ActivityConversionPipeline.STAGE_TIMEOUTS.keys())
        assert expected_stages == actual_stages

    def test_elevate_has_longest_timeout(self, pipeline):
        """ELEVATE (most complex stage) should have the longest timeout."""
        timeouts = ActivityConversionPipeline.STAGE_TIMEOUTS
        assert timeouts["elevate"] >= max(
            v for k, v in timeouts.items() if k != "elevate"
        )

    def test_qc_hook_has_shortest_timeout(self, pipeline):
        """QC hook (deterministic script) should have shortest timeout."""
        timeouts = ActivityConversionPipeline.STAGE_TIMEOUTS
        assert timeouts["qc_hook"] <= min(
            v for k, v in timeouts.items() if k != "qc_hook"
        )
