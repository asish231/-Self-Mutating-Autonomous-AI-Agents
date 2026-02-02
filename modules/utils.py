import os
from typing import Optional, List

class FileSystem:
    """
    A robust utility class for file system operations.
    Provides safe methods for reading, writing, deleting, and checking file existence.
    This module serves as a foundational utility for other agent modules (Action, Perception, etc.).
    """

    def __init__(self, log_func=None):
        """
        Initializes the FileSystem utility.

        Args:
            log_func (Optional[Callable[[str], None]]): A function to use for logging messages.
                                                        If None, a default print-based logger is used.
        """
        self.log = log_func if log_func else self._default_log

    def _default_log(self, message: str):
        """Default logging function if none is provided."""
        print(f"[FileSystem] {message}")

    def read_file(self, filepath: str) -> Optional[str]:
        """
        Reads the content of a file.

        Args:
            filepath (str): The path to the file.

        Returns:
            Optional[str]: The file content if successful, None otherwise.
        """
        if not os.path.exists(filepath):
            self.log(f"Error: File not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.log(f"Successfully read file: {filepath} ({len(content)} chars)")
            return content
        except Exception as e:
            self.log(f"Error reading file {filepath}: {e}")
            return None

    def write_file(self, filepath: str, content: str, mode: str = 'w') -> bool:
        """
        Writes content to a file. Creates directories if necessary.

        Args:
            filepath (str): The path to the file.
            content (str): The content to write.
            mode (str): File write mode ('w' for write, 'a' for append). Defaults to 'w'.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(filepath, mode, encoding="utf-8") as f:
                f.write(content)
            
            self.log(f"Successfully {'appended to' if mode == 'a' else 'wrote to'}: {filepath}")
            return True
        except Exception as e:
            self.log(f"Error writing to file {filepath}: {e}")
            return False

    def delete_file(self, filepath: str) -> bool:
        """
        Deletes a file from the file system.

        Args:
            filepath (str): The path to the file to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not os.path.exists(filepath):
            self.log(f"Warning: File not found, cannot delete: {filepath}")
            return False

        try:
            os.remove(filepath)
            self.log(f"Successfully deleted file: {filepath}")
            return True
        except Exception as e:
            self.log(f"Error deleting file {filepath}: {e}")
            return False

    def exists(self, filepath: str) -> bool:
        """
        Checks if a file or directory exists.

        Args:
            filepath (str): The path to check.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        return os.path.exists(filepath)

    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """
        Lists files in a directory matching a specific pattern.

        Args:
            directory (str): The directory path.
            pattern (str): The file pattern (e.g., "*.py"). Defaults to "*".

        Returns:
            List[str]: A list of matching filenames.
        """
        if not os.path.exists(directory):
            self.log(f"Error: Directory does not exist: {directory}")
            return []

        try:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            # Basic filtering by pattern
            filtered = [f for f in files if f.startswith(pattern.split('*')[0])] 
            return filtered
        except Exception as e:
            self.log(f"Error listing directory {directory}: {e}")
            return []

    def get_file_size(self, filepath: str) -> Optional[int]:
        """
        Gets the size of a file in bytes.

        Args:
            filepath (str): The path to the file.

        Returns:
            Optional[int]: The file size in bytes, or None if file not found.
        """
        if not os.path.exists(filepath):
            return None
        return os.path.getsize(filepath)