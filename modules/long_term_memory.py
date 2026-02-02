import sqlite3
import time
from typing import Callable, List, Dict, Any, Optional
import json

class LongTermMemory:
    """
    Manages the agent's long-term memory, storing structured 'experiences' and observations
    that persist across reboots and provide a richer context for future planning.
    This module extends the basic file system indexing of MemoryManager by
    focusing on semantic and experiential data.
    """

    DB_FILE = "genesis_context.db" # Using the same database as MemoryManager

    def __init__(self, root_dir: str, log_func: Callable[[str], None]):
        """
        Initializes the LongTermMemory module.

        Args:
            root_dir (str): The root directory of the agent, where the database file resides.
            log_func (Callable[[str], None]): A function to use for logging messages.
        """
        self.root_dir = root_dir
        self.log = log_func
        self.db_path = os.path.join(self.root_dir, self.DB_FILE)
        self.db_conn = None # Initialize to None, connect on first use or in _init_db

        self._init_db()
        self.log("LongTermMemory module initialized.")

    def _init_db(self):
        """
        Ensures the 'experiences' table exists in the shared database.
        """
        try:
            self.db_conn = sqlite3.connect(self.db_path)
            cursor = self.db_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    type TEXT NOT NULL,         -- e.g., 'evolution_cycle', 'observation', 'decision', 'reflection'
                    title TEXT NOT NULL,
                    description TEXT,
                    metadata TEXT               -- Store as JSON string for flexibility
                )
            ''')
            self.db_conn.commit()
            self.log(f"LongTermMemory connected to {self.DB_FILE} and ensured 'experiences' table exists.")
        except sqlite3.Error as e:
            self.log(f"Error initializing LongTermMemory database: {e}")
            if self.db_conn:
                self.db_conn.close()
            self.db_conn = None # Mark as failed

    def add_experience(self, type: str, title: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Adds a new structured experience to the long-term memory.

        Args:
            type (str): The category of the experience (e.g., 'evolution_cycle', 'observation', 'decision').
            title (str): A concise title for the experience.
            description (str): A detailed description of the experience.
            metadata (Optional[Dict[str, Any]]): Optional dictionary of additional structured data.

        Returns:
            bool: True if the experience was added successfully, False otherwise.
        """
        if not self.db_conn:
            self.log("Error: Database connection not established for LongTermMemory.")
            return False

        try:
            metadata_str = json.dumps(metadata) if metadata else "{}"
            cursor = self.db_conn.cursor()
            cursor.execute(
                "INSERT INTO experiences (timestamp, type, title, description, metadata) VALUES (?, ?, ?, ?, ?)",
                (time.time(), type, title, description, metadata_str)
            )
            self.db_conn.commit()
            self.log(f"Added new experience: Type='{type}', Title='{title}'")
            return True
        except sqlite3.Error as e:
            self.log(f"Error adding experience to LongTermMemory: {e}")
            return False
        except json.JSONDecodeError as e:
            self.log(f"Error serializing metadata for experience '{title}': {e}")
            return False

    def retrieve_experiences(self, query_type: Optional[str] = None, keyword: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves experiences from long-term memory based on query criteria.
        This is a basic retrieval for now; future versions could use semantic search.

        Args:
            query_type (Optional[str]): Filter by experience type.
            keyword (Optional[str]): Search for a keyword in title or description.
            limit (int): Maximum number of experiences to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing an experience.
        """
        if not self.db_conn:
            self.log("Error: Database connection not established for LongTermMemory.")
            return []

        try:
            cursor = self.db_conn.cursor()
            sql_query = "SELECT timestamp, type, title, description, metadata FROM experiences WHERE 1=1"
            params: List[Any] = []

            if query_type:
                sql_query += " AND type = ?"
                params.append(query_type)
            if keyword:
                sql_query += " AND (title LIKE ? OR description LIKE ?)"
                params.append(f"%{keyword}%")
                params.append(f"%{keyword}%")
            
            sql_query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql_query, tuple(params))
            rows = cursor.fetchall()

            experiences = []
            for row in rows:
                timestamp, type, title, description, metadata_str = row
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except json.JSONDecodeError:
                    self.log(f"Warning: Failed to decode metadata for experience '{title}'. Skipping metadata.")
                    metadata = {}

                experiences.append({
                    "timestamp": timestamp,
                    "type": type,
                    "title": title,
                    "description": description,
                    "metadata": metadata
                })
            self.log(f"Retrieved {len(experiences)} experiences from LongTermMemory.")
            return experiences
        except sqlite3.Error as e:
            self.log(f"Error retrieving experiences from LongTermMemory: {e}")
            return []

    def close(self):
        """Closes the database connection if it's open."""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
            self.log("LongTermMemory database connection closed.")