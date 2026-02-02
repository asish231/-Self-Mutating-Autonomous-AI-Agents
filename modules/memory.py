import os
import sqlite3
import time
from typing import Callable, List, Tuple

class MemoryManager:
    """
    Manages the agent's persistent memory, including indexing the file system
    and retrieving system context from a SQLite database.
    """
    
    DB_FILE = "genesis_context.db"
    MODULES_DIR = "modules" # Directory to scan for other modules

    def __init__(self, root_dir: str, log_func: Callable[[str], None]):
        """
        Initializes the MemoryManager.

        Args:
            root_dir (str): The root directory of the agent.
            log_func (Callable[[str], None]): A function to use for logging messages.
        """
        self.root_dir = root_dir
        self.log = log_func
        self.db_path = os.path.join(self.root_dir, self.DB_FILE)
        self.db_conn = self._init_db()

    def _init_db(self) -> sqlite3.Connection:
        """Initializes the Context Database (SQLite) and returns the connection."""
        self.log(f"Initializing database at {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for file content and modification times
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                content TEXT,
                summary TEXT,
                mtime REAL
            )
        ''')
        # Table for agent memory/logs (separate from agent_life.log for structured events)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                timestamp REAL
            )
        ''')
        conn.commit()
        return conn

    def update_context_index(self):
        """
        Scans the relevant directories (root and modules) and updates the DB
        with file contents and modification times.
        """
        self.log("Indexing file system for context update...")
        cursor = self.db_conn.cursor()
        
        # Directories to scan: root and modules
        paths_to_scan = [self.root_dir]
        modules_full_path = os.path.join(self.root_dir, self.MODULES_DIR)
        if os.path.exists(modules_full_path):
            paths_to_scan.append(modules_full_path)

        for directory in paths_to_scan:
            for filename in os.listdir(directory):
                # Skip database, log files, and backup files
                if filename == self.DB_FILE or filename.endswith(".log") or filename.endswith(".bak"):
                    continue
                # Only include relevant source and documentation files
                if not (filename.endswith(".py") or filename.endswith(".md") or filename.endswith(".json")):
                    continue
                        
                file_full_path = os.path.join(directory, filename)
                relative_path = os.path.relpath(file_full_path, self.root_dir)
                
                try:
                    mtime = os.path.getmtime(file_full_path)
                except FileNotFoundError:
                    self.log(f"Warning: File not found during indexing, skipping: {relative_path}")
                    continue
                
                # Check if update needed based on modification time
                cursor.execute("SELECT mtime FROM files WHERE path=?", (relative_path,))
                row = cursor.fetchone()
                
                if not row or row[0] < mtime:
                    try:
                        with open(file_full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # In a more advanced system, LLM would summarize here. For now, raw content.
                        # The 'summary' column is placeholder for future enhancement.
                        cursor.execute("INSERT OR REPLACE INTO files (path, content, summary, mtime) VALUES (?, ?, ?, ?)",
                                       (relative_path, content, "Raw content", mtime))
                        self.log(f"Indexed/Updated context for: {relative_path}")
                    except Exception as e:
                        self.log(f"Failed to read or index {relative_path}: {e}")
        self.db_conn.commit()

    def get_system_context(self, max_chars: int = 100000) -> str:
        """
        Retrieves the aggregated system context from the database.
        
        Args:
            max_chars (int): Maximum number of characters for the total context string.
                             Helps manage token limits for LLMs.

        Returns:
            str: A concatenated string of file paths and their contents.
        """
        self.log("Retrieving system context...")
        cursor = self.db_conn.cursor()
        # Order by path to ensure consistent context representation
        cursor.execute("SELECT path, content FROM files ORDER BY path ASC")
        rows = cursor.fetchall()
        
        context_parts = []
        current_length = 0
        
        for path, content in rows:
            header = f"\n--- FILE: {path} ---\n"
            
            # Estimate size and truncate content if necessary
            # Leaving some room for headers and other context additions.
            available_for_content = max_chars - current_length - len(header)
            
            if available_for_content <= 0:
                self.log(f"Context limit reached. Truncating context. Skipped: {path}")
                break # Stop adding files if max_chars is hit

            if len(content) > available_for_content:
                # Truncate content, add an ellipsis to indicate truncation
                truncated_content = content[:max(0, available_for_content - 200)] + "\n... [CONTENT TRUNCATED] ...\n"
                context_parts.append(header + truncated_content)
                current_length += len(header) + len(truncated_content)
                self.log(f"Context for {path} truncated. Total length: {current_length}/{max_chars}")
                break # Stop after truncating one file to avoid complex logic and ensure context fits
            else:
                context_parts.append(header + content)
                current_length += len(header) + len(content)
        
        final_context = "".join(context_parts)
        self.log(f"System context retrieved. Total characters: {len(final_context)} (max: {max_chars})")
        return final_context
        
    def add_memory_event(self, event: str):
        """Adds a structured event to the memory table."""
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO memory (event, timestamp) VALUES (?, ?)", (event, time.time()))
        self.db_conn.commit()
        self.log(f"Memory event added: {event}")

    def close(self):
        """Closes the database connection."""
        if self.db_conn:
            self.db_conn.close()
            self.log("Database connection closed.")