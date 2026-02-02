
import os
import sys
import time
import logging
import json
from typing import Optional

# Ensure modules allow relative imports or path setup
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    from modules.core import ModelClientManager
    from modules.memory import MemoryManager
    from modules.self_mutator import SelfMutator
    from modules.planner import AgentPlanner
    from modules.firmware.hal import HAL
    from modules.swarm.manager import SwarmManager
except ImportError as e:
    print(f"CRITICAL BOOT ERROR: Missing modules: {e}")
    sys.exit(1)

# Configure Logging
log_file = os.path.join(script_dir, "agent_life.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("GENESIS.KERNEL")

CONFIG_FILE = "config.json"

class GenesisKernel:
    """
    The Central Nervous System of the Swarm.
    Orchestrates the Agents, maintains Memory, and plans Evolution.
    """
    def __init__(self):
        self.root_dir = script_dir
        self.script_path = os.path.abspath(__file__)
        self.logger = logger
        
        self.logger.info("--- Boot sequence initiated ---")
        
        self.config = self._load_config()
        
        # Initialize Core Modules
        self.client_manager = ModelClientManager(self.config, self.log_wrapper)
        self.memory_manager = MemoryManager(self.root_dir, self.log_wrapper)
        self.self_mutator = SelfMutator(self.root_dir, self.script_path, self.log_wrapper)
        self.planner = AgentPlanner(self.client_manager, self.log_wrapper)
        
        # Initialize Firmware (HAL) & Swarm
        self.hal = HAL(self.log_wrapper)
        self.swarm = SwarmManager(self.hal, self.log_wrapper)
        
        self.logger.info("Kernel initialized successfully.")

    def log_wrapper(self, msg: str):
        """Adapter for modules that expect a callable logger."""
        self.logger.info(msg)

    def _load_config(self) -> dict:
        path = os.path.join(self.root_dir, CONFIG_FILE)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def run_cycle(self):
        self.logger.info("--- Genesis Cycle Start ---")
        
        # 1. Update Context
        self.memory_manager.update_context_index()
        context = self.memory_manager.get_system_context()
        self.memory_manager.add_memory_event("Cycle started.")
        
        # 2. Plan Next Move (AgentPlanner)
        system_prompt, user_prompt = self.planner.formulate_next_llm_query(context)
        
        # 3. Execute Decision (Call LLM)
        try:
            self.logger.info("Consulting Intelligence...")
            response = self.client_manager.call(system_prompt, user_prompt)
            
            # 4. Apply Changes (Mutator) OR Delegate (Swarm)
            # The Planner directs the output. If it's code, Mutator handles it.
            # If it's an 'action' script, the Swarm (ExecutorAgent) will pick it up automatically.
            
            self.self_mutator.apply_evolution(response)
            self.memory_manager.add_memory_event("Evolution applied.")
            
        except Exception as e:
            self.logger.error(f"Cycle failed: {e}")
            self.memory_manager.add_memory_event(f"Failure: {e}")
            time.sleep(10) # Backoff

    def boot(self):
        # Start the Swarm (Agents)
        self.swarm.bootstrap()
        
        # Enter Main Loop
        try:
            while True:
                self.run_cycle()
                self.logger.info("Cycle complete. Sleeping 60s...")
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Kernel shutting down.")

if __name__ == "__main__":
    kernel = GenesisKernel()
    kernel.boot()