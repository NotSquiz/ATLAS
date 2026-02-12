"""
Tests for SkillExecutor CLI retry logic (D111).
"""

import subprocess
import unittest.mock

import pytest

from atlas.orchestrator.skill_executor import SkillExecutor


@pytest.fixture
def executor():
    """SkillExecutor in CLI mode with CLI check stubbed."""
    e = SkillExecutor(use_api=False)
    e._check_cli_available = lambda: True
    return e


class TestCliRetryOnTransientFailure:
    """D111: _execute_cli retries once on fast transient failures."""

    @pytest.mark.asyncio
    async def test_retries_on_fast_exit_code_1(self, executor):
        """Fast exit-code-1 failure should trigger one retry."""
        fail_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )
        success_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="output", stderr=""
        )

        with unittest.mock.patch("atlas.orchestrator.skill_executor.subprocess.run") as mock_run:
            mock_run.side_effect = [fail_result, success_result]
            with unittest.mock.patch("asyncio.sleep", new_callable=unittest.mock.AsyncMock):
                raw, tokens, dur, error = await executor._execute_cli(
                    "test prompt", "test system", timeout=30
                )

        assert error is None
        assert raw == "output"
        assert mock_run.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_success(self, executor):
        """Successful first call should not retry."""
        success_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="output", stderr=""
        )

        with unittest.mock.patch("atlas.orchestrator.skill_executor.subprocess.run") as mock_run:
            mock_run.return_value = success_result
            raw, tokens, dur, error = await executor._execute_cli(
                "test prompt", "test system", timeout=30
            )

        assert error is None
        assert mock_run.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_error_after_retry_exhausted(self, executor):
        """If retry also fails, return the error."""
        fail_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="something broke"
        )

        with unittest.mock.patch("atlas.orchestrator.skill_executor.subprocess.run") as mock_run:
            mock_run.return_value = fail_result
            with unittest.mock.patch("asyncio.sleep", new_callable=unittest.mock.AsyncMock):
                raw, tokens, dur, error = await executor._execute_cli(
                    "test prompt", "test system", timeout=30
                )

        assert error is not None
        assert "exit code 1" in error
        assert "something broke" in error
        assert mock_run.call_count == 2


class TestCliErrorDiagnostics:
    """D111: Error messages include useful diagnostic info."""

    @pytest.mark.asyncio
    async def test_error_includes_stderr(self, executor):
        """Error message should include stderr when present."""
        fail_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="API rate limit"
        )

        with unittest.mock.patch("atlas.orchestrator.skill_executor.subprocess.run") as mock_run:
            mock_run.return_value = fail_result
            with unittest.mock.patch("asyncio.sleep", new_callable=unittest.mock.AsyncMock):
                _, _, _, error = await executor._execute_cli(
                    "test prompt", "test system", timeout=30
                )

        assert "API rate limit" in error

    @pytest.mark.asyncio
    async def test_error_includes_stdout_when_no_stderr(self, executor):
        """Error should include stdout snippet when stderr is empty."""
        fail_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="Error: connection reset", stderr=""
        )

        with unittest.mock.patch("atlas.orchestrator.skill_executor.subprocess.run") as mock_run:
            mock_run.return_value = fail_result
            with unittest.mock.patch("asyncio.sleep", new_callable=unittest.mock.AsyncMock):
                _, _, _, error = await executor._execute_cli(
                    "test prompt", "test system", timeout=30
                )

        assert "connection reset" in error

    @pytest.mark.asyncio
    async def test_error_empty_streams(self, executor):
        """Both streams empty should still produce useful message."""
        fail_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )

        with unittest.mock.patch("atlas.orchestrator.skill_executor.subprocess.run") as mock_run:
            mock_run.return_value = fail_result
            with unittest.mock.patch("asyncio.sleep", new_callable=unittest.mock.AsyncMock):
                _, _, _, error = await executor._execute_cli(
                    "test prompt", "test system", timeout=30
                )

        assert "exit code 1" in error
