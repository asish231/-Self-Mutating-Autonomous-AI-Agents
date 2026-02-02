import os
import subprocess
import platform
import shutil
from typing import List, Optional, Tuple

class HAL:
    """
    Hardware Abstraction Layer (Firmware).
    Provides a unified, safe interface for Agents to interact with the Host OS.
    """
    
    def __init__(self, log_func):
        self.log = log_func
        self.os_type = platform.system()
        
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Safely executes a shell command with timeout."""
        try:
            # SECURITY: In a real scenario, we would have a whitelist here.
            # For now, we trust the swarm, but log heavily.
            self.log(f"HAL: Executing command: {command}")
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr
            
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", "Command timed out."
        except Exception as e:
            return -1, "", str(e)

    def read_file(self, path: str) -> Optional[str]:
        """Reads a file safely."""
        try:
            if not os.path.exists(path): return None
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            self.log(f"HAL: Read error {path}: {e}")
            return None

    def write_file(self, path: str, content: str) -> bool:
        """Writes a file safely, creating dirs if needed."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            self.log(f"HAL: Write error {path}: {e}")
            return False
    
    def get_system_info(self) -> dict:
        """Returns low-level system stats."""
        return {
            "os": self.os_type,
            "release": platform.release(),
            "cpu_count": os.cpu_count(),
            "cwd": os.getcwd()
        }
