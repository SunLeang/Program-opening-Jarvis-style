"""Cross-platform program launcher."""
from typing import List, Dict
import subprocess
import platform
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProgramLauncher:
    """Reads config program entries and executes OS-specific commands asynchronously."""
    
    def __init__(self, config_programs: List[Dict[str, str]]) -> None:
        self.config_programs = config_programs
        self.os_type = platform.system()

    def _select_command(self, program: Dict[str, str]) -> str:
        """Return the appropriate CLI command based on current OS.
        
        Raises:
            ValueError: If OS key is missing from program config.
        """
        raise NotImplementedError

    def launch_all(self) -> List[str]:
        """Spawn all programs concurrently. Returns list of successfully launched names."""
        raise NotImplementedError

    def _run_detached(self, cmd: str) -> subprocess.Popen:
        """Execute command with new process group to prevent child-process blocking."""
        raise NotImplementedError