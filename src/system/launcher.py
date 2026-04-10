"""Cross-platform program launcher."""
import subprocess
import platform
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ProgramLauncher:
    """Reads config program entries and executes OS-specific commands asynchronously."""
    
    def __init__(self, config_programs: List[Dict[str, str]]) -> None:
        self.config_programs = config_programs
        self.os_type = platform.system()

    def _select_command(self, program: Dict[str, str]) -> str:
        """Return the appropriate CLI command based on current OS.
        
        Raises:
            KeyError: If the command key for the current OS is missing.
        """
        key_map = {"Windows": "windows_cmd", "Linux": "linux_cmd", "Darwin": "linux_cmd"}
        os_key = key_map.get(self.os_type)
        
        if not os_key:
            raise ValueError(f"Unsupported OS for launch routing: {self.os_type}")
            
        cmd = program.get(os_key)
        if not cmd:
            raise KeyError(f"Missing '{os_key}' for program: {program.get('name', 'UNKNOWN')}")
            
        return cmd.strip()

    def _run_detached(self, cmd: str) -> subprocess.Popen:
        """Execute command in a new process group/session to prevent blocking or inheriting stdio."""
        kwargs: dict = {"shell": True}
        
        if self.os_type == "Windows":
            # Prevents CMD windows from flashing for GUI apps
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        else:
            # Detaches from parent process group so apps survive if main script exits
            kwargs["start_new_session"] = True
            
        return subprocess.Popen(cmd, **kwargs)

    def launch_all(self) -> List[str]:
        """Spawn all programs concurrently. Returns list of successfully launched names."""
        launched_names: List[str] = []
        
        for prog in self.config_programs:
            prog_name = prog.get("name", "UNKNOWN")
            try:
                cmd = self._select_command(prog)
                logger.info(f"[LAUNCH] {prog_name} -> '{cmd}'")
                self._run_detached(cmd)
                launched_names.append(prog_name)
            except (ValueError, KeyError) as e:
                logger.warning(f"[SKIP] {prog_name}: {e}")
            except Exception as e:
                logger.error(f"[FAIL] {prog_name}: {e}")
                
        return launched_names
