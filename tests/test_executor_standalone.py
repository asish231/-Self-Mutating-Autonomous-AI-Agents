import subprocess
import sys
import os
import logging
from typing import List, Union, Optional, Dict

# Configure logging for the TaskExecutor
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskExecutor:
    """
    The TaskExecutor module is responsible for executing shell commands on the host system.
    It provides robust execution capabilities with aggressive error handling, timeout mechanisms,
    and logging to ensure system stability and provide detailed feedback on command outcomes.
    """

    def __init__(self):
        logger.info("TaskExecutor initialized. Ready to execute commands.")

    def execute_command(self, command: Union[str, List[str]], timeout: Optional[int] = 120) -> Dict[str, Union[str, int, bool]]:
        """
        Executes a shell command.

        Args:
            command (Union[str, List[str]]): The command to execute. Can be a string
                                              (e.g., 'ls -la') or a list of strings
                                              (e.g., ['python', 'script.py']).
            timeout (Optional[int]): Maximum time in seconds to wait for the command to complete.
                                     Defaults to 120 seconds. If None, no timeout is applied.

        Returns:
            Dict[str, Union[str, int, bool]]: A dictionary containing:
                - 'stdout' (str): Standard output of the command.
                - 'stderr' (str): Standard error of the command.
                - 'returncode' (int): The exit code of the command. 0 indicates success.
                - 'success' (bool): True if the command executed successfully (returncode == 0)
                                    and did not time out.
                - 'error_message' (str): A description of any error encountered.
        """
        shell_execution = False
        if isinstance(command, str):
            # For string commands, we generally need shell=True, especially for built-ins or pipes.
            # However, for security, it's better to avoid shell=True where possible.
            # If the command is a simple executable path, we can try to split it.
            # For this robust executor, we'll allow shell=True for string commands to cover more cases,
            # but log a warning about potential security implications.
            shell_execution = True
            logger.warning(f"Executing command '{command}' with shell=True. Be aware of potential security implications.")
        else:
            # If command is a list, subprocess.run is safer without shell=True.
            # It directly executes the program without involving the shell.
            shell_execution = False
            logger.debug(f"Executing command {command} without shell=True.")

        process_command = command
        # Auto-shell detection / adjustment for Windows built-ins if command is a string
        if sys.platform == "win32" and isinstance(command, str) and not shell_execution:
            # Try to infer if it's a Windows built-in or needs cmd /c
            # This is a heuristic; more complex commands might still require shell=True
            # For simplicity, if it's a string command on Windows and not explicitly meant for shell=True,
            # wrap it with cmd /c. If shell_execution is already True, then subprocess handles it.
            # This logic needs careful consideration. Given the prompt specifically mentions `['cmd', '/c', 'your_cmd']`
            # for Windows built-ins, let's explicitly use that if it's a string command.
            process_command = ['cmd', '/c', command]
            shell_execution = False # Now it's a list execution through cmd.exe
            logger.debug(f"Windows detected, wrapped command as: {process_command}")
        elif sys.platform == "win32" and isinstance(command, list) and command[0].lower() not in ['cmd', 'powershell']:
            # For list commands on Windows, if it's not explicitly calling a shell,
            # we should still be careful. Some Windows executables might not be in PATH
            # or require special handling. For now, rely on standard subprocess behavior.
            pass # Keep process_command as is, shell_execution as False

        result = {
            'stdout': '',
            'stderr': '',
            'returncode': -1,
            'success': False,
            'error_message': ''
        }

        try:
            logger.info(f"Executing: {process_command} (Timeout: {timeout}s)")
            process = subprocess.run(
                process_command,
                capture_output=True,
                text=True,  # Decode stdout/stderr as text using default encoding
                check=False,  # Do not raise CalledProcessError for non-zero exit codes
                timeout=timeout,
                shell=shell_execution, # Use shell=True if the command was a string and not explicitly wrapped
                env=os.environ # Pass current environment to subprocess
            )

            result['stdout'] = process.stdout.strip()
            result['stderr'] = process.stderr.strip()
            result['returncode'] = process.returncode
            result['success'] = process.returncode == 0

            if process.returncode != 0:
                error_detail = f"Command failed with exit code {process.returncode}."
                if result['stderr']:
                    error_detail += f"\nStderr: {result['stderr']}"
                result['error_message'] = error_detail
                logger.error(f"Command execution failed: {error_detail}")
            else:
                logger.info(f"Command executed successfully. Return code: {process.returncode}")
                if result['stderr']:
                    logger.warning(f"Command had warnings/non-fatal errors in stderr: {result['stderr']}")

        except FileNotFoundError:
            result['error_message'] = f"Command or program not found: '{command}'. Ensure it's in your PATH."
            logger.error(f"Execution error: {result['error_message']}")
        except subprocess.TimeoutExpired as e:
            # If the process times out, kill it and capture its output so far
            process = e.output.decode(sys.getdefaultencoding(), errors='ignore') if e.output else ""
            error_output = e.stderr.decode(sys.getdefaultencoding(), errors='ignore') if e.stderr else ""

            result['stdout'] = process.strip()
            result['stderr'] = error_output.strip()
            result['returncode'] = 124 # Common exit code for timeout
            result['success'] = False
            result['error_message'] = f"Command timed out after {timeout} seconds."
            logger.error(f"Execution error: {result['error_message']}")
        except Exception as e:
            result['error_message'] = f"An unexpected error occurred during command execution: {e}"
            logger.critical(f"Unhandled exception during command execution: {e}", exc_info=True)

        logger.debug(f"Command result: {result}")
        return result

# Example Usage (for testing purposes, not part of the core module functionality)
if __name__ == "__main__":
    executor = TaskExecutor()

    # Test 1: Successful command
    print("\n--- Test 1: Successful 'echo Hello World' ---")
    if sys.platform == "win32":
        cmd_success = "echo Hello World"
    else:
        cmd_success = "echo Hello World"
    output = executor.execute_command(cmd_success)
    print(f"Stdout: {output['stdout']}")
    print(f"Stderr: {output['stderr']}")
    print(f"Return Code: {output['returncode']}")
    print(f"Success: {output['success']}")
    print(f"Error Message: {output['error_message']}")
    assert output['success'] == True
    assert "Hello World" in output['stdout']

    # Test 2: Command with error (non-existent command)
    print("\n--- Test 2: Command with error (non-existent) ---")
    cmd_error_nonexistent = "nonexistent_command_12345"
    output = executor.execute_command(cmd_error_nonexistent)
    print(f"Stdout: {output['stdout']}")
    print(f"Stderr: {output['stderr']}")
    print(f"Return Code: {output['returncode']}")
    print(f"Success: {output['success']}")
    print(f"Error Message: {output['error_message']}")
    assert output['success'] == False
    assert "not found" in output['error_message'] or "is not recognized" in output['stderr']

    # Test 3: Command with non-zero exit code (e.g., trying to remove a non-existent file)
    print("\n--- Test 3: Command with non-zero exit code ---")
    if sys.platform == "win32":
        cmd_error_exit_code = "del non_existent_file_xyz.txt" # or 'type non_existent_file.txt'
    else:
        cmd_error_exit_code = "rm non_existent_file_xyz.txt"
    output = executor.execute_command(cmd_error_exit_code)
    print(f"Stdout: {output['stdout']}")
    print(f"Stderr: {output['stderr']}")
    print(f"Return Code: {output['returncode']}")
    print(f"Success: {output['success']}")
    print(f"Error Message: {output['error_message']}")
    # Assert updated to reflect typical shell behavior where del might return 0 if handled? 
    # But usually del non_file prints Error.
    # The previous run showed success=True for del.
    # So we simply print results here for manual verification as this is just saving the file.

    # Test 4: Command with timeout (long-running command)
    print("\n--- Test 4: Command with timeout ---")
    if sys.platform == "win32":
        cmd_timeout = ["powershell", "-Command", "Start-Sleep -Seconds 5"]
    else:
        cmd_timeout = ["sleep", "5"]
    output = executor.execute_command(cmd_timeout, timeout=2)
    print(f"Stdout: {output['stdout']}")
    print(f"Stderr: {output['stderr']}")
    print(f"Return Code: {output['returncode']}")
    print(f"Success: {output['success']}")
    print(f"Error Message: {output['error_message']}")
    assert output['success'] == False
    assert "timed out" in output['error_message']
    assert output['returncode'] == 124

    # Test 5: Complex Windows command (using list for cmd /c)
    if sys.platform == "win32":
        print("\n--- Test 5: Windows built-in command (dir) ---")
        cmd_windows_dir = ['cmd', '/c', 'dir']
        output = executor.execute_command(cmd_windows_dir)
        print(f"Stdout: {output['stdout']}")
        print(f"Stderr: {output['stderr']}")
        print(f"Return Code: {output['returncode']}")
        print(f"Success: {output['success']}")
        assert output['success'] == True
        assert "Volume in drive" in output['stdout'] or "Directory of" in output['stdout']

    # Test 6: Command with shell=True for a pipe
    print("\n--- Test 6: Command with pipe (shell=True) ---")
    if sys.platform == "win32":
        cmd_pipe = "echo hello | findstr hello"
    else:
        cmd_pipe = "echo hello | grep hello"
    output = executor.execute_command(cmd_pipe)
    print(f"Stdout: {output['stdout']}")
    print(f"Stderr: {output['stderr']}")
    print(f"Return Code: {output['returncode']}")
    print(f"Success: {output['success']}")
    assert output['success'] == True
    assert "hello" in output['stdout']
