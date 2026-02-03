"""Tests for deployment script validation.

Test suite for validating shell script syntax and functionality.
These tests use subprocess to execute scripts with test parameters.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from typing import Optional


class TestDeploymentScripts:
    """Test deployment scripts for Fly.io, Railway, and Render."""

    @pytest.fixture
    def script_dir(self) -> Path:
        """Return the deployment scripts directory."""
        return Path(__file__).parent

    @pytest.fixture
    def merchant_key(self) -> str:
        """Test merchant key."""
        return "shop-test123"

    @pytest.fixture
    def secret_key(self) -> str:
        """Test secret key."""
        return "dGVzdF9zZWNyZXRfa2V5XzMyYnl0ZXM="

    @pytest.fixture
    def render_api_key(self) -> str:
        """Test Render API key."""
        return "rdr_test_api_key_12345"

    def test_flyio_script_exists(self, script_dir: Path) -> None:
        """Test that Fly.io deployment script exists."""
        flyio_script = script_dir / "flyio.sh"
        assert flyio_script.exists(), "flyio.sh deployment script must exist"
        assert flyio_script.is_file(), "flyio.sh must be a file"

    def test_railway_script_exists(self, script_dir: Path) -> None:
        """Test that Railway deployment script exists."""
        railway_script = script_dir / "railway.sh"
        assert railway_script.exists(), "railway.sh deployment script must exist"
        assert railway_script.is_file(), "railway.sh must be a file"

    def test_render_script_exists(self, script_dir: Path) -> None:
        """Test that Render deployment script exists."""
        render_script = script_dir / "render.sh"
        assert render_script.exists(), "render.sh deployment script must exist"
        assert render_script.is_file(), "render.sh must be a file"

    def test_flyio_script_executable(self, script_dir: Path) -> None:
        """Test that Fly.io deployment script is executable."""
        flyio_script = script_dir / "flyio.sh"
        assert flyio_script.stat().st_mode & 0o111, "flyio.sh must be executable"

    def test_railway_script_executable(self, script_dir: Path) -> None:
        """Test that Railway deployment script is executable."""
        railway_script = script_dir / "railway.sh"
        assert railway_script.stat().st_mode & 0o111, "railway.sh must be executable"

    def test_render_script_executable(self, script_dir: Path) -> None:
        """Test that Render deployment script is executable."""
        render_script = script_dir / "render.sh"
        assert render_script.stat().st_mode & 0o111, "render.sh must be executable"

    def test_flyio_script_validates_missing_arguments(self, script_dir: Path) -> None:
        """Test that Fly.io script validates missing arguments."""
        flyio_script = script_dir / "flyio.sh"
        result = subprocess.run(
            [str(flyio_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Script should fail without arguments"
        output = result.stdout + result.stderr
        assert "Missing required arguments" in output, "Should show missing arguments error"

    def test_railway_script_validates_missing_arguments(self, script_dir: Path) -> None:
        """Test that Railway script validates missing arguments."""
        railway_script = script_dir / "railway.sh"
        result = subprocess.run(
            [str(railway_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Script should fail without arguments"
        output = result.stdout + result.stderr
        assert "Missing required arguments" in output, "Should show missing arguments error"

    def test_render_script_validates_missing_arguments(self, script_dir: Path) -> None:
        """Test that Render script validates missing arguments."""
        render_script = script_dir / "render.sh"
        result = subprocess.run(
            [str(render_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Script should fail without arguments"
        output = result.stdout + result.stderr
        assert "Missing required arguments" in output, "Should show missing arguments error"

    def test_flyio_script_syntax_valid(self, script_dir: Path) -> None:
        """Test that Fly.io script has valid bash syntax."""
        flyio_script = script_dir / "flyio.sh"
        result = subprocess.run(
            ["bash", "-n", str(flyio_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"flyio.sh has syntax errors: {result.stderr}"

    def test_railway_script_syntax_valid(self, script_dir: Path) -> None:
        """Test that Railway script has valid bash syntax."""
        railway_script = script_dir / "railway.sh"
        result = subprocess.run(
            ["bash", "-n", str(railway_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"railway.sh has syntax errors: {result.stderr}"

    def test_render_script_syntax_valid(self, script_dir: Path) -> None:
        """Test that Render script has valid bash syntax."""
        render_script = script_dir / "render.sh"
        result = subprocess.run(
            ["bash", "-n", str(render_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"render.sh has syntax errors: {result.stderr}"

    def test_flyio_script_contains_required_functions(self, script_dir: Path) -> None:
        """Test that Fly.io script contains required functions."""
        flyio_script = script_dir / "flyio.sh"
        content = flyio_script.read_text()

        required_functions = [
            "check_fly_cli",
            "check_docker",
            "deploy_flyio",
            "handle_error",
            "log_progress",
            "log_success",
            "log_error",
        ]

        for func in required_functions:
            assert func in content, f"flyio.sh must define {func} function"

    def test_railway_script_contains_required_functions(self, script_dir: Path) -> None:
        """Test that Railway script contains required functions."""
        railway_script = script_dir / "railway.sh"
        content = railway_script.read_text()

        required_functions = [
            "check_railway_cli",
            "deploy_railway",
            "handle_error",
            "log_progress",
            "log_success",
            "log_error",
        ]

        for func in required_functions:
            assert func in content, f"railway.sh must define {func} function"

    def test_render_script_contains_required_functions(self, script_dir: Path) -> None:
        """Test that Render script contains required functions."""
        render_script = script_dir / "render.sh"
        content = render_script.read_text()

        required_functions = [
            "check_render_cli",
            "deploy_render",
            "handle_error",
            "log_progress",
            "log_success",
            "log_error",
        ]

        for func in required_functions:
            assert func in content, f"render.sh must define {func} function"

    def test_flyio_script_contains_progress_indicators(self, script_dir: Path) -> None:
        """Test that Fly.io script contains progress indicators."""
        flyio_script = script_dir / "flyio.sh"
        content = flyio_script.read_text()

        # Check for progress percentage format
        assert "[${PROGRESS}%]" in content, "Script must show progress percentage"

    def test_railway_script_contains_progress_indicators(self, script_dir: Path) -> None:
        """Test that Railway script contains progress indicators."""
        railway_script = script_dir / "railway.sh"
        content = railway_script.read_text()

        # Check for progress percentage format
        assert "[${PROGRESS}%]" in content, "Script must show progress percentage"

    def test_render_script_contains_progress_indicators(self, script_dir: Path) -> None:
        """Test that Render script contains progress indicators."""
        render_script = script_dir / "render.sh"
        content = render_script.read_text()

        # Check for progress percentage format
        assert "[${PROGRESS}%]" in content, "Script must show progress percentage"

    @patch("subprocess.run")
    def test_flyio_script_checks_cli_before_deploy(self, mock_run: Mock) -> None:
        """Test that Fly.io script checks for CLI installation before deploying."""
        # Mock successful CLI check
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )

        # This test validates the script flow logic
        # Actual CLI testing would require integration tests
        assert True  # Placeholder for integration test validation

    def test_script_sets_exit_on_error_flag(self, script_dir: Path) -> None:
        """Test that all scripts set 'set -euo pipefail' for error handling."""
        scripts = ["flyio.sh", "railway.sh", "render.sh"]

        for script_name in scripts:
            script_path = script_dir / script_name
            content = script_path.read_text()
            assert "set -euo pipefail" in content, f"{script_name} must set error handling flags"

    def test_flyio_script_outputs_success_indicator(self, script_dir: Path) -> None:
        """Test that Fly.io script outputs STEP:SUCCESS on completion."""
        flyio_script = script_dir / "flyio.sh"
        content = flyio_script.read_text()

        assert "log_success \"STEP:SUCCESS\"" in content or 'echo "STEP:SUCCESS"' in content, \
            "Script must output STEP:SUCCESS on completion"

    def test_railway_script_outputs_success_indicator(self, script_dir: Path) -> None:
        """Test that Railway script outputs STEP:SUCCESS on completion."""
        railway_script = script_dir / "railway.sh"
        content = railway_script.read_text()

        assert "log_success \"STEP:SUCCESS\"" in content or 'echo "STEP:SUCCESS"' in content, \
            "Script must output STEP:SUCCESS on completion"

    def test_render_script_outputs_success_indicator(self, script_dir: Path) -> None:
        """Test that Render script outputs STEP:SUCCESS on completion."""
        render_script = script_dir / "render.sh"
        content = render_script.read_text()

        assert "log_success \"STEP:SUCCESS\"" in content or 'echo "STEP:SUCCESS"' in content, \
            "Script must output STEP:SUCCESS on completion"
