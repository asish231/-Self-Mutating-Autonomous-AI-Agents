import time
import threading
import uuid
from abc import ABC, abstractmethod
from modules.firmware.hal import HAL

class BaseAgent(ABC, threading.Thread):
    """
    Abstract Base Class for all Swarm Agents.
    Runs in its own thread, has access to Firmware (HAL), and a communication channel.
    """
    
    def __init__(self, name: str, hal: HAL, log_func):
        super().__init__()
        self.agent_id = str(uuid.uuid4())[:8]
        self.name = name
        self.hal = hal
        self._log = log_func
        self.running = False
        self.daemon = True # Kill if main process dies

    def log(self, msg: str):
        self._log(f"[{self.name}:{self.agent_id}] {msg}")

    def run(self):
        """Main loop for the agent."""
        self.running = True
        self.log("Started.")
        try:
            while self.running:
                self.loop()
                time.sleep(5) # Default tick
        except Exception as e:
            self.log(f"Crashed: {e}")
        finally:
            self.log("Stopped.")

    def stop(self):
        self.running = False

    @abstractmethod
    def loop(self):
        """The specific logic for this agent type. Must be implemented by subclasses."""
        pass
