import os
import threading
import time
from typing import Dict, Any, Callable, List, Optional

class MultiAgentCoordinator:
    """
    Manages coordination and communication between multiple autonomous agents.
    This module is designed to facilitate the interaction, task distribution,
    and monitoring of a collective of Genesis Kernel instances or specialized sub-agents.
    """

    def __init__(self, log_func: Optional[Callable[[str], None]] = None):
        """
        Initializes the MultiAgentCoordinator.

        Args:
            log_func (Optional[Callable[[str], None]]): A function to use for logging messages.
                                                        If None, a default print-based logger is used.
        """
        self.log = log_func if log_func else self._default_log
        self.registered_agents: Dict[str, Dict[str, Any]] = {} # Agent ID -> Agent Metadata
        self.agent_lock = threading.Lock() # To ensure thread-safe access to registered_agents
        self.log("MultiAgentCoordinator initialized.")

    def _default_log(self, message: str):
        """Default logging function if none is provided."""
        print(f"[MultiAgentCoordinator] {message}")

    def register_agent(self, agent_id: str, capabilities: List[str], initial_status: str = "idle") -> bool:
        """
        Registers a new agent with the coordinator.

        Args:
            agent_id (str): A unique identifier for the agent.
            capabilities (List[str]): A list of capabilities the agent possesses (e.g., ["networking", "file_io"]).
            initial_status (str): The initial status of the agent (e.g., "idle", "busy").

        Returns:
            bool: True if registration was successful, False if agent_id already exists.
        """
        with self.agent_lock:
            if agent_id in self.registered_agents:
                self.log(f"Agent '{agent_id}' already registered.")
                return False
            self.registered_agents[agent_id] = {
                "capabilities": capabilities,
                "status": initial_status,
                "last_seen": time.time(),
                "tasks": [] # List of assigned tasks
            }
            self.log(f"Agent '{agent_id}' registered with capabilities: {', '.join(capabilities)}")
            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregisters an agent from the coordinator.

        Args:
            agent_id (str): The unique identifier of the agent to unregister.

        Returns:
            bool: True if unregistration was successful, False if agent_id was not found.
        """
        with self.agent_lock:
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]
                self.log(f"Agent '{agent_id}' unregistered.")
                return True
            self.log(f"Attempted to unregister unknown agent: '{agent_id}'.")
            return False

    def update_agent_status(self, agent_id: str, new_status: str, task_id: Optional[str] = None) -> bool:
        """
        Updates the status of a registered agent.

        Args:
            agent_id (str): The unique identifier of the agent.
            new_status (str): The new status for the agent.
            task_id (Optional[str]): The ID of the task the agent is currently handling, if any.

        Returns:
            bool: True if status was updated, False if agent_id not found.
        """
        with self.agent_lock:
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id]["status"] = new_status
                self.registered_agents[agent_id]["last_seen"] = time.time()
                if task_id:
                    if task_id not in self.registered_agents[agent_id]["tasks"]:
                        self.registered_agents[agent_id]["tasks"].append(task_id)
                self.log(f"Agent '{agent_id}' status updated to '{new_status}' (Task: {task_id or 'None'}).")
                return True
            self.log(f"Attempted to update status for unknown agent: '{agent_id}'.")
            return False

    def get_available_agents(self, required_capabilities: Optional[List[str]] = None) -> List[str]:
        """
        Retrieves a list of agents that are currently 'idle' and possess the required capabilities.

        Args:
            required_capabilities (Optional[List[str]]): A list of capabilities an agent must have.

        Returns:
            List[str]: A list of agent IDs that match the criteria.
        """
        available = []
        with self.agent_lock:
            for agent_id, data in self.registered_agents.items():
                if data["status"] == "idle":
                    if required_capabilities:
                        if all(cap in data["capabilities"] for cap in required_capabilities):
                            available.append(agent_id)
                    else:
                        available.append(agent_id)
        self.log(f"Found {len(available)} available agents matching criteria.")
        return available

    def assign_task(self, agent_id: str, task_description: Dict[str, Any]) -> bool:
        """
        Assigns a task to a specific agent and updates its status.
        This is a placeholder for a more complex task distribution mechanism.

        Args:
            agent_id (str): The ID of the agent to assign the task to.
            task_description (Dict[str, Any]): A dictionary describing the task.
                                               Expected to contain at least a "task_id".

        Returns:
            bool: True if task was assigned, False otherwise (e.g., agent not found or not idle).
        """
        if "task_id" not in task_description:
            self.log("Error: Task description must contain a 'task_id'.")
            return False

        with self.agent_lock:
            if agent_id in self.registered_agents and self.registered_agents[agent_id]["status"] == "idle":
                task_id = task_description["task_id"]
                self.registered_agents[agent_id]["tasks"].append(task_id)
                self.registered_agents[agent_id]["status"] = "busy"
                self.log(f"Task '{task_id}' assigned to agent '{agent_id}'.")
                # In a real system, you'd send the task to the agent here (e.g., via IPC, message queue, network).
                return True
            self.log(f"Could not assign task to agent '{agent_id}'. Agent not found or not idle.")
            return False

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves information about a specific registered agent."""
        with self.agent_lock:
            return self.registered_agents.get(agent_id)

    def heartbeat(self, agent_id: str) -> bool:
        """
        Updates the 'last_seen' timestamp for a given agent, indicating it's still active.

        Args:
            agent_id (str): The unique identifier of the agent.

        Returns:
            bool: True if heartbeat was recorded, False if agent not found.
        """
        with self.agent_lock:
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id]["last_seen"] = time.time()
                # self.log(f"Heartbeat received from agent '{agent_id}'.") # Too verbose for a log, perhaps.
                return True
            self.log(f"Heartbeat from unknown agent: '{agent_id}'.")
            return False

    def monitor_agents(self, timeout_seconds: int = 300):
        """
        Periodically checks for agents that haven't sent a heartbeat within the timeout.
        Marks inactive agents or takes other recovery actions.
        This method would typically run in a separate thread or be called periodically.

        Args:
            timeout_seconds (int): The number of seconds after which an agent is considered inactive.
        """
        self.log(f"Monitoring agents for inactivity (timeout: {timeout_seconds}s).")
        current_time = time.time()
        agents_to_remove = []
        with self.agent_lock:
            for agent_id, data in self.registered_agents.items():
                if (current_time - data["last_seen"]) > timeout_seconds:
                    self.log(f"Agent '{agent_id}' detected as inactive (last seen {current_time - data['last_seen']:.1f}s ago).")
                    # For now, just log and mark for removal. Future: attempt reconnection, reassign tasks.
                    agents_to_remove.append(agent_id)
        
        for agent_id in agents_to_remove:
            self.unregister_agent(agent_id) # Consider different states like "inactive" vs "unregistered"