import pytest
import platform
import subprocess
from unittest.mock import patch, MagicMock
from src.system.launcher import ProgramLauncher

@pytest.fixture
def mock_popen():
    """Mock Popen to prevent actual system calls during tests."""
    with patch("src.system.launcher.subprocess.Popen") as mock:
        mock.return_value = MagicMock()
        yield mock

class TestProgramLauncher:
    def test_windows_routing(self, mock_popen):
        """Verify 'windows_cmd' is selected and detached correctly on Windows."""
        config = [{"name": "VSCode", "windows_cmd": "code", "linux_cmd": "code"}]
        with patch.object(platform, "system", return_value="Windows"):
            launcher = ProgramLauncher(config)
            result = launcher.launch_all()
            
        assert result == ["VSCode"]
        mock_popen.assert_called_once()
        _, kwargs = mock_popen.call_args
        assert kwargs["shell"] is True
        assert kwargs.get("creationflags") == getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def test_linux_routing(self, mock_popen):
        """Verify 'linux_cmd' is selected with session isolation on Linux."""
        config = [{"name": "YT", "windows_cmd": "start yt", "linux_cmd": "xdg-open yt"}]
        with patch.object(platform, "system", return_value="Linux"):
            launcher = ProgramLauncher(config)
            result = launcher.launch_all()
            
        assert result == ["YT"]
        mock_popen.assert_called_once()
        _, kwargs = mock_popen.call_args
        assert kwargs["start_new_session"] is True

    def test_missing_os_key_raises_error(self):
        """Gracefully fail if config omits current OS command."""
        bad_config = [{"name": "Missing", "linux_cmd": "code"}]
        with patch.object(platform, "system", return_value="Windows"):
            launcher = ProgramLauncher(bad_config)
            with pytest.raises(KeyError):
                launcher._select_command(bad_config[0])

    def test_graceful_skip_on_execution_failure(self, mock_popen, caplog):
        """Ensure one broken command doesn't crash the batch."""
        mock_popen.side_effect = FileNotFoundError("Binary not found")
        config = [{"name": "Fail", "windows_cmd": "x", "linux_cmd": "y"}]
        with patch.object(platform, "system", return_value="Linux"):
            launcher = ProgramLauncher(config)
            result = launcher.launch_all()
            
        assert result == []
        assert "[FAIL] Fail:" in caplog.text
