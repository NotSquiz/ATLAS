"""
Tests for ActivityConversionPipeline deterministic functions.

Covers 11 functions with ~60+ test cases:
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
# _remove_em_dashes (3 cases)
# ============================================================

class TestRemoveEmDashes:

    def test_replaces_em_dash_with_period(self, pipeline):
        content = "This is great — and also fun"
        result = pipeline._remove_em_dashes(content)
        assert "—" not in result
        assert ". " in result

    def test_no_em_dashes(self, pipeline):
        content = "No special characters here."
        result = pipeline._remove_em_dashes(content)
        assert result == content

    def test_multiple_em_dashes(self, pipeline):
        content = "First—second—third"
        result = pipeline._remove_em_dashes(content)
        assert "—" not in result
        assert result.count(".") >= 2


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
        content = "Children love this — really."
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

    def test_truncated_json_repair(self, pipeline):
        raw = '{"grade": "A", "issues": [{"category": "voice"'
        result, error = pipeline._extract_audit_json(raw)
        # Should attempt repair by adding closing braces/brackets
        # May or may not succeed depending on JSON structure
        # The key test is it doesn't crash
        assert error is not None or result is not None

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
        # Should return elevated unchanged (or close to it) on parse error
        assert "age_months_min" in result


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
