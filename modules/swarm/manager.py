import os
import glob
import importlib.util
from typing import Dict
from modules.firmware.hal import HAL
from modules.swarm.base_agent import BaseAgent
from modules.executor import TaskExecutor

# --- Sample Agent Implementations (for bootstrapping) ---
class SystemAgent(BaseAgent):
    def loop(self):
        # Monitor system stats
        # self.hal.get_system_info()
        pass

class ArchitectAgent(BaseAgent):
    """
    Specialist agent focused on swarm expansion and architectural evolution.
    It proposes and creates new agent types.
    """
    def loop(self):
        self.log("ArchitectAgent: Analyzing swarm health and mission goals...")
        pass

class ExecutorAgent(BaseAgent):
    """
    Specialist agent that watches for 'actions/*.py' scripts and executes them.
    This creates the 'Action Loop' where the Kernel writes a script and this Agent runs it.
    """
    def __init__(self, name: str, hal: HAL, log_func):
        super().__init__(name, hal, log_func)
        self.executor = TaskExecutor(log_func)
        self.actions_dir = "actions"
        if not os.path.exists(self.actions_dir):
            os.makedirs(self.actions_dir)
        self.log("ExecutorAgent: Action directory initialized.")

    def loop(self):
        # 1. Look for .py files in actions/
        scripts = glob.glob(os.path.join(self.actions_dir, "*.py"))
        
        for script_path in scripts:
            # 2. Check if it's already "processed" (renamed to .done)
            if script_path.endswith(".done.py"):
                continue

            self.log(f"ExecutorAgent: Found new action script: {script_path}")
            
            # 3. Execute the script via subprocess (safer than import)
            exit_code, stdout, stderr = self.executor.execute_command(["python", script_path], timeout=30)
            
            result_str = f"\n## Execution Result: {os.path.basename(script_path)}\n"
            if exit_code == 0:
                result_str += f"**Status**: SUCCESS\n**Output**:\n```\n{stdout}\n```\n"
                self.log(f"Action Success: {script_path}")
            else:
                result_str += f"**Status**: FAILED\n**Error**:\n```\n{stderr}\n```\n"
                self.log(f"Action Failed: {script_path}")

            # 4. Log to persistent memory file for Planner to see
            with open("execution_results.md", "a", encoding="utf-8") as f:
                f.write(result_str)

            # 5. Mark as done
            new_path = script_path.replace(".py", ".done.py")
            os.rename(script_path, new_path)
            self.log(f"Marked {script_path} as done.")


class SwarmManager:
    """
    Manages the lifecycle of all agents in the Swarm.
    """
    def __init__(self, hal: HAL, log_func):
        self.hal = hal
        self.log = log_func
        self.agents: Dict[str, BaseAgent] = {}

    def spawn_agent(self, agent_class, name_prefix: str):
        """Spawns a new agent instance."""
        name = f"{name_prefix}_{len(self.agents) + 1}"
        agent = agent_class(name, self.hal, self.log)
        self.agents[agent.agent_id] = agent
        agent.start()
        self.log(f"Swarm: Spawned {name} ({agent.agent_id})")

    def kill_agent(self, agent_id: str):
        if agent_id in self.agents:
            self.agents[agent_id].stop()
            del self.agents[agent_id]
            self.log(f"Swarm: Killed agent {agent_id}")

    def bootstrap(self):
        """Starts the initial set of agents."""
        self.log("Swarm: Bootstrapping...")
        # Start a System Monitor
        self.spawn_agent(SystemAgent, "SystemMonitor")
        # Start the Architect
        self.spawn_agent(ArchitectAgent, "Architect")
        # Start the Executor
        self.spawn_agent(ExecutorAgent, "Executor")


