import os
from typing import Optional, Dict, Any, List, Tuple, Callable

# Assuming NetworkManager, FileSystem, and TaskExecutor are in their respective modules
from modules.networking import NetworkManager
from modules.utils import FileSystem
from modules.executor import TaskExecutor

class ActionModule:
    """
    Provides the Genesis Kernel with capabilities to perform actions in its environment.
    This module centralizes functions for interacting with the local file system,
    external web sources, and executing system commands, leveraging existing utility modules.
    It acts as the primary interface for the agent to enact its decisions.
    """

    def __init__(self, log_func: Optional[Callable[[str], None]] = None):
        """
        Initializes the ActionModule.

        Args:
            log_func (Optional[Callable[[str], None]]): A function to use for logging messages.
                                                        If None, a default print-based logger is used.
        """
        self.log = log_func if log_func else self._default_log
        self.file_system = FileSystem(log_func=self.log)
        self.network_manager = NetworkManager(log_func=self.log)
        self.task_executor = TaskExecutor(log_func=self.log)
        self.log("ActionModule initialized, integrating FileSystem, NetworkManager, and TaskExecutor.")

    def _default_log(self, message: str):
        """Default logging function if none is provided."""
        print(f"[ActionModule] {message}")

    def execute_shell_command(self, command: List[str], timeout: int = 60, use_whitelist: bool = True) -> Tuple[int, str, str]:
        """
        Executes a system shell command using the TaskExecutor.

        Args:
            command (List[str]): The command and its arguments as a list (e.g., ["ls", "-la"]).
            timeout (int): Maximum time in seconds to wait for the command to complete.
            use_whitelist (bool): If True, only whitelisted commands can be executed.

        Returns:
            Tuple[int, str, str]: A tuple containing (exit_code, stdout, stderr).
                                  exit_code: 0 for success, non-zero for failure or error.
                                  stdout: Standard output of the command.
                                  stderr: Standard error of the command.
        """
        self.log(f"Executing system command: {' '.join(command)}")
        exit_code, stdout, stderr = self.task_executor.execute_command(command, timeout, use_whitelist)
        if exit_code == 0:
            self.log(f"Command '{' '.join(command)}' completed successfully.")
        else:
            self.log(f"Command '{' '.join(command)}' failed with exit code {exit_code}. Stderr: {stderr.strip()}")
        return exit_code, stdout, stderr

    def create_or_update_file(self, filepath: str, content: str, append: bool = False) -> bool:
        """
        Creates a new file or updates an existing one with the given content.
        If `append` is True, content is added to the end of the file.

        Args:
            filepath (str): The path to the file.
            content (str): The content to write to the file.
            append (bool): If true, appends to the file; otherwise, overwrites.

        Returns:
            bool: True if the file operation was successful, False otherwise.
        """
        self.log(f"{'Appending to' if append else 'Writing to'} file: {filepath}")
        mode = 'a' if append else 'w'
        success = self.file_system.write_file(filepath, content, mode=mode)
        if success:
            self.log(f"Successfully {'appended to' if append else 'wrote to'} {filepath}.")
        else:
            self.log(f"Failed to {'append to' if append else 'write to'} {filepath}.")
        return success

    def delete_file(self, filepath: str) -> bool:
        """
        Deletes a file from the file system.

        Args:
            filepath (str): The path to the file to delete.

        Returns:
            bool: True if the file was deleted, False otherwise.
        """
        self.log(f"Attempting to delete file: {filepath}")
        success = self.file_system.delete_file(filepath)
        if success:
            self.log(f"Successfully deleted {filepath}.")
        else:
            self.log(f"Failed to delete file: {filepath}.")
        return success

    def download_file(self, url: str, dest_filepath: str) -> bool:
        """
        Downloads a file from a given URL to a specified destination.

        Args:
            url (str): The URL of the file to download.
            dest_filepath (str): The local path where the file should be saved.

        Returns:
            bool: True if the download was successful, False otherwise.
        """
        self.log(f"Attempting to download file from {url} to {dest_filepath}")
        response_text = self.network_manager.get(url, stream=True) # Use stream for large files
        if response_text:
            try:
                # Assuming get returns a requests.Response object when stream=True
                with open(dest_filepath, 'wb') as f:
                    for chunk in response_text.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.log(f"Successfully downloaded {url} to {dest_filepath}.")
                return True
            except Exception as e:
                self.log(f"Error saving downloaded file to {dest_filepath}: {e}")
                return False
        else:
            self.log(f"Failed to download file from {url}.")
            return False

    def send_get_request(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Sends an HTTP GET request and returns the response text.

        Args:
            url (str): The URL for the GET request.
            params (Optional[Dict[str, Any]]): Dictionary of URL parameters.
            headers (Optional[Dict[str, str]]): Dictionary of HTTP headers.

        Returns:
            Optional[str]: The response text if successful, None otherwise.
        """
        self.log(f"Sending GET request to: {url}")
        response = self.network_manager.get(url, params=params, headers=headers)
        if response:
            self.log(f"GET request to {url} successful.")
        else:
            self.log(f"GET request to {url} failed.")
        return response

    def send_post_request(self, url: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Sends an HTTP POST request and returns the response text.

        Args:
            url (str): The URL for the POST request.
            data (Optional[Dict[str, Any]]): Dictionary, bytes, or file-like object to send in the body (form-encoded).
            json_data (Optional[Dict[str, Any]]): A JSON serializable dictionary to send in the body.
            headers (Optional[Dict[str, str]]): Dictionary of HTTP headers.

        Returns:
            Optional[str]: The response text if successful, None otherwise.
        """
        self.log(f"Sending POST request to: {url}")
        response = self.network_manager.post(url, data=data, json_data=json_data, headers=headers)
        if response:
            self.log(f"POST request to {url} successful.")
        else:
            self.log(f"POST request to {url} failed.")
        return response

    # Future additions:
    # - `upload_file(filepath: str, url: str, field_name: str = 'file', headers: Optional[Dict[str, str]] = None) -> Optional[str]`: For uploading files.
    # - `interact_with_multi_agent(agent_id: str, message: Dict[str, Any]) -> bool`: For structured communication with other agents.
    # - `run_python_code(code_string: str) -> Tuple[int, str, str]`: For executing Python code snippets in a subprocess.