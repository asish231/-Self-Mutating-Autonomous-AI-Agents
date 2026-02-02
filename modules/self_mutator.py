import os
import sys
import ast
import shutil
import time
from typing import Callable

class SelfMutator:
    """
    Manages the mutation and rebirth of the Genesis Kernel.
    It validates code, creates backups, and handles the recursive restart.
    """

    def __init__(self, root_dir: str, script_path: str, logger: Callable[[str], None]):
        """
        Initializes the SelfMutator.

        Args:
            root_dir (str): The root directory of the agent.
            script_path (str): The absolute path to the main evolve_agent.py file.
            logger (Callable[[str], None]): A logging function.
        """
        self.root_dir = root_dir
        self.script_path = script_path
        self.log = logger
        self.log("SelfMutator module initialized.")

    def apply_evolution(self, llm_response: str):
        """
        Parses LLM response, extracts the filename and code, 
        validates syntax, and writes to disk.
        """
        self.log("Initiating mutation sequence...")
        
        try:
            # 1. Parsing the multi-part response
            lines = llm_response.split('\n')
            filename = None
            code_lines = []
            parsing_code = False
            
            for line in lines:
                if line.startswith("FILENAME:"):
                    filename = line.replace("FILENAME:", "").strip()
                elif line.strip() == "CODE:":
                    parsing_code = True
                elif parsing_code:
                    code_lines.append(line)
            
            if not filename or not code_lines:
                # Fallback: Maybe the LLM didn't use markers? 
                # If so, we assume it's updating the kernel itself.
                filename = os.path.basename(self.script_path)
                code_content = llm_response
            else:
                code_content = "\n".join(code_lines)

            # 2. Syntax Validation
            if not self._validate_syntax(code_content):
                self.log(f"CRITICAL: Syntax validation failed for {filename}. Mutation rejected.")
                raise ValueError(f"Generated code for {filename} contains syntax errors.")

            # 3. Snapshotting: Create Backup (only for the target file if it exists)
            full_path = os.path.join(self.root_dir, filename)
            if os.path.exists(full_path):
                backup_path = self._create_backup(full_path)
                self.log(f"Backup created: {backup_path}")

            # 4. Write to disk
            
            # CRITICAL SECURITY CHECK: Prevent overwrite of the Kernel (evolve_agent.py) by generated actions
            if filename == os.path.basename(self.script_path):
                self.log(f"SECURITY ALERT: Attempt to overwrite Kernel ({filename}) blocked.")
                # We do NOT write. We just return.
                return

            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code_content)
            self.log(f"Genesis successful: {filename} updated.")

            # 5. Rebirth: (Logic disabled as we don't allow kernel overwrite anymore basically)
            # If we ever re-enable kernel updates, it should be via a specific 'admin' flag or separate process.
            # if filename == os.path.basename(self.script_path):
            #     self.log("Kernel update detected. Initiating rebirth...")
            #     self._restart_agent()

        except Exception as e:
            self.log(f"Mutation failed: {e}")
            raise

    def _validate_syntax(self, code: str) -> bool:
        """
        Validates the Python code using AST parsing.
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            self.log(f"Syntax Error detected: {e}")
            return False

    def _create_backup(self, target_path: str) -> str:
        """
        Creates a timestamped backup in a hidden .backups folder.
        """
        backup_dir = os.path.join(self.root_dir, ".backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d%H%M%S")
        filename = os.path.basename(target_path)
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_name)
        
        shutil.copy2(target_path, backup_path)
        return backup_path


    def _cleanup_old_backups(self):
        """
        Maintains a rolling window of the 3 most recent backup files.
        """
        try:
            # Get all .bak files in the root directory
            bak_files = [f for f in os.listdir(self.root_dir) if f.endswith('.bak')]
            
            # Sort by modification time (oldest first)
            bak_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.root_dir, x)))
            
            # Delete all except the last 3
            for old_file in bak_files[:-3]:
                file_path = os.path.join(self.root_dir, old_file)
                os.remove(file_path)
                self.log(f"Deleted old backup: {old_file}")
                
        except Exception as e:
            self.log(f"Error during backup cleanup: {e}")

    def _restart_agent(self):
        """
        Restarts the agent process by executing the current script again.
        This effectively 'reboots' the agent with the new code.
        """
        python = sys.executable
        # os.execv replaces the current process with the new executable
        os.execv(python, [python] + sys.argv)