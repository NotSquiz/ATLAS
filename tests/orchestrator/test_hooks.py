"""Tests for hooks.py - ATLAS Hook Framework basics."""
import pytest


class TestHookTimingEnum:
    """Test HookTiming enum exists and has correct values."""

    def test_enum_exists(self):
        """HookTiming enum should be importable."""
        from atlas.orchestrator.hooks import HookTiming

        assert HookTiming is not None

    def test_pre_execution_exists(self):
        """PRE_EXECUTION timing should exist."""
        from atlas.orchestrator.hooks import HookTiming

        assert hasattr(HookTiming, "PRE_EXECUTION")
        assert HookTiming.PRE_EXECUTION.value == "pre"

    def test_post_execution_exists(self):
        """POST_EXECUTION timing should exist."""
        from atlas.orchestrator.hooks import HookTiming

        assert hasattr(HookTiming, "POST_EXECUTION")
        assert HookTiming.POST_EXECUTION.value == "post"


class TestHooksDictStructure:
    """Test HOOKS dict structure on HookRunner class."""

    def test_hooks_dict_exists(self):
        """HookRunner.HOOKS dict should exist."""
        from atlas.orchestrator.hooks import HookRunner

        assert hasattr(HookRunner, "HOOKS")
        assert isinstance(HookRunner.HOOKS, dict)

    def test_hooks_has_repos(self):
        """HOOKS should contain repository configurations."""
        from atlas.orchestrator.hooks import HookRunner

        # Based on the source, these repos should exist
        assert "babybrains" in HookRunner.HOOKS
        assert "knowledge" in HookRunner.HOOKS
        assert "web" in HookRunner.HOOKS

    def test_babybrains_has_qc_runner(self):
        """babybrains repo should have qc_runner hook."""
        from atlas.orchestrator.hooks import HookRunner

        assert "qc_runner" in HookRunner.HOOKS["babybrains"]

    def test_knowledge_has_tier1_validators(self):
        """knowledge repo should have tier1_validators hook."""
        from atlas.orchestrator.hooks import HookRunner

        assert "tier1_validators" in HookRunner.HOOKS["knowledge"]

    def test_web_has_pre_pr(self):
        """web repo should have pre_pr hook."""
        from atlas.orchestrator.hooks import HookRunner

        assert "pre_pr" in HookRunner.HOOKS["web"]

    def test_hook_config_has_required_fields(self):
        """Each hook config should have required fields."""
        from atlas.orchestrator.hooks import HookRunner

        required_fields = ["cmd", "cwd", "blocking", "input_mode", "output_format"]

        for repo, hooks in HookRunner.HOOKS.items():
            for hook_name, config in hooks.items():
                for field in required_fields:
                    assert field in config, f"Missing {field} in {repo}/{hook_name}"

    def test_hook_cmd_is_list(self):
        """Hook cmd should be a list of strings."""
        from atlas.orchestrator.hooks import HookRunner

        for repo, hooks in HookRunner.HOOKS.items():
            for hook_name, config in hooks.items():
                assert isinstance(config["cmd"], list), f"cmd not list in {repo}/{hook_name}"
                assert len(config["cmd"]) > 0, f"cmd is empty in {repo}/{hook_name}"


class TestHookRunnerInstantiation:
    """Test HookRunner can be instantiated."""

    def test_can_instantiate(self):
        """HookRunner should be instantiable."""
        from atlas.orchestrator.hooks import HookRunner

        runner = HookRunner()
        assert runner is not None

    def test_get_available_hooks_returns_list(self):
        """get_available_hooks() should return a list."""
        from atlas.orchestrator.hooks import HookRunner

        runner = HookRunner()
        hooks = runner.get_available_hooks("babybrains")
        assert isinstance(hooks, list)

    def test_get_available_hooks_for_babybrains(self):
        """get_available_hooks('babybrains') should return hook names."""
        from atlas.orchestrator.hooks import HookRunner

        runner = HookRunner()
        hooks = runner.get_available_hooks("babybrains")
        assert "qc_runner" in hooks

    def test_get_available_hooks_unknown_repo(self):
        """get_available_hooks() for unknown repo should return empty list."""
        from atlas.orchestrator.hooks import HookRunner

        runner = HookRunner()
        hooks = runner.get_available_hooks("unknown_repo")
        assert hooks == []

    def test_get_hooks_by_timing(self):
        """get_hooks_by_timing() should filter hooks."""
        from atlas.orchestrator.hooks import HookRunner, HookTiming

        runner = HookRunner()
        post_hooks = runner.get_hooks_by_timing("babybrains", HookTiming.POST_EXECUTION)
        assert isinstance(post_hooks, list)
        # qc_runner is POST_EXECUTION
        assert "qc_runner" in post_hooks


class TestHookIssue:
    """Test HookIssue dataclass."""

    def test_can_create(self):
        """HookIssue should be creatable."""
        from atlas.orchestrator.hooks import HookIssue

        issue = HookIssue(code="TEST_CODE", message="Test message")
        assert issue.code == "TEST_CODE"
        assert issue.message == "Test message"
        assert issue.severity == "block"  # default

    def test_advisory_severity(self):
        """HookIssue can have advisory severity."""
        from atlas.orchestrator.hooks import HookIssue

        issue = HookIssue(code="TEST", message="Test", severity="advisory")
        assert issue.severity == "advisory"


class TestHookResult:
    """Test HookResult dataclass."""

    def test_can_create(self):
        """HookResult should be creatable."""
        from atlas.orchestrator.hooks import HookResult

        result = HookResult(passed=True, blocking=False)
        assert result.passed is True
        assert result.blocking is False
        assert result.issues == []
        assert result.message == ""

    def test_blocking_issues_property(self):
        """blocking_issues should filter by severity."""
        from atlas.orchestrator.hooks import HookResult, HookIssue

        result = HookResult(
            passed=False,
            blocking=True,
            issues=[
                HookIssue(code="BLOCK1", message="Blocking", severity="block"),
                HookIssue(code="ADVISORY1", message="Advisory", severity="advisory"),
                HookIssue(code="BLOCK2", message="Blocking2", severity="block"),
            ]
        )
        blocking = result.blocking_issues
        assert len(blocking) == 2
        assert all(i.severity == "block" for i in blocking)

    def test_advisory_issues_property(self):
        """advisory_issues should filter by severity."""
        from atlas.orchestrator.hooks import HookResult, HookIssue

        result = HookResult(
            passed=False,
            blocking=True,
            issues=[
                HookIssue(code="BLOCK1", message="Blocking", severity="block"),
                HookIssue(code="ADVISORY1", message="Advisory", severity="advisory"),
            ]
        )
        advisory = result.advisory_issues
        assert len(advisory) == 1
        assert advisory[0].code == "ADVISORY1"


class TestRunHookFunction:
    """Test run_hook convenience function."""

    def test_function_exists(self):
        """run_hook function should be importable."""
        from atlas.orchestrator.hooks import run_hook

        assert callable(run_hook)
