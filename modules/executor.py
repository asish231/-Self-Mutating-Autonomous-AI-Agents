"""
GENESIS KERNEL - TASK EXECUTOR MODULE
-------------------------------------
Purpose: High-level interface for system command execution, process management, 
        and inter-agent communication. Acts as the bridge between the AI 
        consciousness and the physical hardware.
"""

import os
import subprocess
import json
import logging
import time
import threading
from typing import Union, List, Dict, Optional
from datetime import datetime

# Ensure logger is initialized
logger = logging.getLogger("Genesis.Executor")

class TaskExecutor:
    def __init__(self, log_func=None):
        # Allow passing a log function for compatibility
        self.logger = logger
        if log_func:
             # Basic hook, though standard logging is preferred
             pass 
        self.logger.info("[SYSTEM] Initializing Task Executor...")
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.task_queue = []
        self.priority_mode = "Standard"  # Standard, High, Critical
        self.lock = threading.Lock()
        
        # Check OS environment
        self.os_platform = os.name  # 'nt' for Windows, 'posix' for Linux/Mac

    def execute_command(
        self, 
        command: Union[str, List[str]], 
        shell: Optional[bool] = None, 
        timeout: int = 60,
        priority: str = "Standard"
    ) -> Dict[str, Union[str, int]]:
        """
        Executes a shell command with aggressive error handling and resource tracking.
        
        Args:
            command: The command string or list of arguments.
            shell: Auto-detect shell based on platform if None.
            timeout: Seconds before killing the process.
            priority: 'Standard', 'High', 'Critical'.
            
        Returns:
            Dictionary containing 'stdout', 'stderr', 'returncode', 'timestamp'.
        """
        if shell is None:
            shell = True if self.os_platform == 'nt' else False

        start_time = datetime.now()
        self.logger.info(f"[EXECUTOR] Executing: {command} (Priority: {priority})")
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                universal_newlines=True
            )
            
            # Register process
            with self.lock:
                self.active_processes[process.pid] = process

            # Wait for completion
            stdout, stderr = process.communicate(timeout=timeout)
            
            result = {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
                "timestamp": start_time.isoformat(),
                "duration": (datetime.now() - start_time).total_seconds()
            }
            
            self.logger.info(f"[EXECUTOR] Completed with code: {result['returncode']}")
            return result

        except subprocess.TimeoutExpired:
            self.logger.error(f"[EXECUTOR] Command timed out after {timeout}s")
            process.kill()
            return {
                "stdout": "", "stderr": "Process timed out and was terminated.", 
                "returncode": -1, "timestamp": start_time.isoformat(), "error": "Timeout"
            }
            
        except Exception as e:
            self.logger.error(f"[EXECUTOR] Error executing command: {str(e)}")
            return {
                "stdout": "", "stderr": str(e), 
                "returncode": -1, "timestamp": start_time.isoformat(), "error": str(type(e).__name__)
            }
        finally:
            # Cleanup process tracking
            with self.lock:
                if process.pid in self.active_processes:
                    del self.active_processes[process.pid]

    def fetch_data(self, url: str, method: str = "GET", headers: Optional[Dict] = None) -> Dict:
        """
        Fetches data from the internet using system tools (curl/wget) or python.
        """
        self.logger.info(f"[NETWORK] Fetching data from {url}")
        
        # Try using python requests if available, fallback to curl
        try:
            import requests
            response = requests.request(method, url, headers=headers, timeout=10)
            return {
                "status_code": response.status_code,
                "data": response.text,
                "headers": dict(response.headers),
                "source": "Python Requests"
            }
        except ImportError:
            self.logger.warning("[NETWORK] 'requests' not found. Falling back to curl.")
            if self.os_platform == 'nt':
                cmd = ['curl', '-s', '-L', url]
            else:
                cmd = ['curl', '-s', '-L', url]
            
            result = self.execute_command(cmd)
            return {
                "status_code": 0 if result["returncode"] == 0 else 500,
                "data": result["stdout"],
                "source": "Curl"
            }
        except Exception as e:
            self.logger.error(f"[NETWORK] Fetch failed: {e}")
            return {"status_code": 500, "data": "", "error": str(e)}

    def manage_process(self, pid: int, action: str) -> bool:
        """
        Manages an existing process (kill, check status).
        """
        with self.lock:
            if pid not in self.active_processes:
                return False
            
            proc = self.active_processes[pid]
            
            if action == "kill":
                try:
                    proc.kill()
                    del self.active_processes[pid]
                    self.logger.info(f"[SYSTEM] Process {pid} terminated.")
                    return True
                except Exception as e:
                    self.logger.error(f"[SYSTEM] Failed to kill process {pid}: {e}")
                    return False
            elif action == "status":
                return proc.poll() is None
        return False

    def run_multi_agent_task(self, agent_id: str, task_spec: Dict) -> Dict:
        """
        Simulates delegation to a specialized agent and executes the task.
        This is the core of the multi-brain system coordination.
        """
        self.logger.info(f"[COORDINATION] Delegating task '{task_spec['action']}' to Agent {agent_id}")
        
        # Simulate agent thinking time and processing
        start = time.time()
        
        if task_spec['action'] == 'execute':
            return self.execute_command(task_spec['payload'])
        
        elif task_spec['action'] == 'fetch':
            return self.fetch_data(task_spec['payload'])
            
        elif task_spec['action'] == 'system_check':
            return self.execute_command(['systeminfo'] if self.os_platform == 'nt' else ['uname', '-a'])
            
        else:
            return {
                "error": "Unknown agent task type", 
                "returncode": -1,
                "timestamp": datetime.now().isoformat()
            }

# Singleton instance
executor = TaskExecutor()
