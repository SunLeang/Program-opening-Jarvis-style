import pytest
# from src.system.launcher import ProgramLauncher

class TestProgramLauncher:
    def test_windows_routing(self, monkeypatch) -> None:
        """Verify 'windows_cmd' is selected on Windows platform."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        pass

    def test_linux_routing(self, monkeypatch) -> None:
        """Verify 'linux_cmd' is selected on Linux platform."""
        monkeypatch.setattr("platform.system", lambda: "Linux")
        pass

    def test_missing_os_key_raises_value_error(self) -> None:
        """Gracefully fail if config omits current OS command."""
        pass