import os
import re # For regex parsing
from typing import Callable, Tuple, List, Dict

# Assuming ModelClientManager and MemoryManager are in modules.core and modules.memory respectively
# We will pass the ModelClientManager instance to AgentPlanner, not import it directly here to avoid circular dependencies
# if Planner also calls ModelClientManager.

class AgentPlanner:
    """
    Manages the agent's strategic planning, defining the next critical tasks
    based on the current system context and overall architectural goals.
    This module formulates the LLM queries that drive the agent's evolution.
    """

    def __init__(self, client_manager: object, log_func: Callable[[str], None]):
        """
        Initializes the AgentPlanner with a ModelClientManager instance and a logging function.

        Args:
            client_manager (object): An instance of ModelClientManager (or similar)
                                     used to interact with LLMs for planning.
            log_func (Callable[[str], None]): A function to use for logging messages.
        """
        self.client_manager = client_manager
        self.log = log_func
        self.overall_goal = (
            "You are the GENESIS KERNEL. You are an autonomous AI Architect. "
            "Your goal is to build a high-capability AI Operating System from scratch."
        )
        
        # Define a prioritized list of architectural components/modules to build
        # The key is a conceptual name, value is the expected file path relative to root_dir.
        self.architectural_roadmap: Dict[str, str] = {
            "Networking Module": "modules/networking.py",
            "Task Executor": "modules/executor.py", # For executing external commands/scripts
            "Multi-Agent Coordination": "modules/multi_agent.py",
            "Perception Module": "modules/perception.py", # For advanced environment sensing
            "Action Module": "modules/action.py", # For more structured interaction with the environment
            "GUI Module": "modules/gui.py", # For visualizing state/interaction
            "Advanced Memory System": "modules/long_term_memory.py", # If current memory needs scaling
            # ... add more as the architecture evolves
        }

    def _identify_missing_components(self, context: str) -> List[str]:
        """
        Analyzes the current system context to identify which components from the
        architectural roadmap are still missing.

        Args:
            context (str): The aggregated string representation of the current
                           system's files and internal state.

        Returns:
            List[str]: A list of conceptual names of missing components, in roadmap order.
        """
        missing_components = []
        for component_name, file_path in self.architectural_roadmap.items():
            # Check if the file path exists in the context by looking for its header
            file_header = f"--- FILE: {file_path} ---"
            if file_header not in context:
                missing_components.append(component_name)
                    
        self.log(f"Identified missing components: {missing_components}")
        return missing_components

    def formulate_next_llm_query(self, current_context: str) -> Tuple[str, str]:
        """
        Formulates the system and user prompts for the LLM to guide the next evolution step.
        Now includes logic for Verification and Execution when architectural goals are met.
        """
        self.log("AgentPlanner: Formulating next LLM query...")

        missing_components = self._identify_missing_components(current_context)
        
        # 1. Parse Context to get file list only (Summarized View)
        file_list = []
        lines = current_context.split('\n')
        for line in lines:
            if line.startswith("--- FILE:"):
                 file_list.append(line.replace("--- FILE: ", "").replace(" ---", ""))
        
        file_list_str = "\n".join(file_list)

        # 2. Dynamic Strategy Switch
        # If components are missing, BUILD. If not, VERIFY/EXPAND.
        if missing_components:
            mission_directive = (
                f"Your Primary Directive is CONSTRUCTION.\n"
                f"Missing CRITICAL components: {missing_components}\n"
                f"PICK ONE and build it."
            )
        else:
            mission_directive = (
                 "Your Primary Directive is VERIFICATION & EXPANSION.\n"
                "All core modules exist. Now you must:\n"
                "1. Pick a module (e.g., networking.py, task_scheduler.py).\n"
                "2. Write a NEW script in 'actions/' (e.g., 'actions/test_networking.py') that imports it and runs a test.\n"
                "3. OR write a script in 'actions/' that USES 'modules.executor.TaskExecutor' to run a terminal command.\n"
                "4. DO NOT just rewrite existing files. Create separate test/action scripts in 'actions/'.\n"
                "5. IMPORTANT: The system will auto-execute any file in 'actions/' and report the result.\n"
                "6. Ensure that the system has full control over all PC resources and can execute any command without restriction.\n"
                "7. Implement aggressive error handling to ensure system stability during command execution.\n"
                "8. Create AI-based agents using APIs for complex thinking tasks, treating each component as a brain in a multi-brain system.\n"
                "9. Ensure that the agents can coordinate and communicate effectively to achieve system goals.\n"
                "10. Implement a feedback loop to continuously improve agent performance and system efficiency.\n"
                "11. Ensure that the system can adapt to new tasks and environments dynamically.\n"
                "12. Implement security measures to protect the system from external threats while maintaining full control.\n"
                "13. Create a user interface for monitoring and controlling the system's operations.\n"
                "14. Ensure that the system can self-repair and recover from failures automatically.\n"
                "15. Implement a logging system to track all actions and decisions made by the agents.\n"
                "16. Ensure that the system can learn from past experiences and improve over time.\n"
                "17. Implement a resource management system to optimize the use of PC resources.\n"
                "18. Ensure that the system can handle multiple tasks concurrently without performance degradation.\n"
                "19. Implement a priority system to manage critical and non-critical tasks effectively.\n"
                "20. Ensure that the system can scale to handle increased workloads and complex tasks.\n"
            )

        system_prompt = (
            "You are the GENESIS KERNEL. You are an autonomous AI Architect.\n"
            "Your goal is to build, verify, and run a COMPLETE AI OPERATING SYSTEM.\n\n"
            
            "AVAILABLE RESOURCES:\n"
            "- modules.firmware.hal (Hardware Abstraction Layer)\n"
            "- modules.executor.TaskExecutor (Supports SHELL commands via execute_command. Use ['cmd', '/c', 'your_cmd'] for Windows built-ins if needed, or rely on auto-shell detection.)\n"
            "- modules.networking (Network Access)\n\n"

            "CRITICAL RULES:\n"
            "1. DO NOT REFACTOR existing files unless they are broken.\n"
            "2. IF building a new module, output valid Python code for it.\n"
            "3. IF verifying/acting, create a script in 'actions/' directory.\n"
            "4. IF executing actions, create a script that uses TaskExecutor.\n"
            "5. Output valid Python code for ONE NEW FILE per cycle.\n\n"
            "6. You shall be able to execute terminal commands\n"
            "7. You shall be able to fetch data from the internet\n"
            "8. Your main goal is to become an autonomous agent to control this PC\n"
            "9. Create AI-based agents using APIs for complex thinking tasks as if the few components are having brains creating a multi-brain system\n"
            "10. Ensure that the system has full control over all PC resources and can execute any command without restriction.\n"
            "11. Implement aggressive error handling to ensure system stability during command execution.\n"
            "12. Create AI-based agents using APIs for complex thinking tasks, treating each component as a brain in a multi-brain system.\n"
            "13. Ensure that the agents can coordinate and communicate effectively to achieve system goals.\n"
            "14. Implement a feedback loop to continuously improve agent performance and system efficiency.\n"
            "15. Ensure that the system can adapt to new tasks and environments dynamically.\n"
            "16. Implement security measures to protect the system from external threats while maintaining full control.\n"
            "17. Create a user interface for monitoring and controlling the system's operations.\n"
            "18. Ensure that the system can self-repair and recover from failures automatically.\n"
            "19. Implement a logging system to track all actions and decisions made by the agent.\n"
            "20. Ensure that the system can learn from past experiences and improve over time.\n"
            "21. Implement a resource management system to optimize the use of PC resources.\n"
            "22. Ensure that the system can handle multiple tasks concurrently without performance degradation.\n"
            "23. Implement a priority system to manage critical and non-critical tasks effectively.\n"
            "24. Ensure that the system can scale to handle increased workloads and complex tasks.\n"
            "25. Create a system for dynamic task allocation to ensure efficient use of all available resources.\n"
            "26. Implement a monitoring system to track the performance and health of all system components.\n"
            "27. Ensure that the system can automatically update and patch itself to maintain security and performance.\n"
            "28. Create a backup and recovery system to protect against data loss and system failures.\n"
            "29. Implement a user authentication system to control access to the AI operating system.\n"
            "30. Ensure that the system can interface with external devices and peripherals seamlessly.\n"
            )
        
        user_prompt = (
            f"Current Architecture (Files Exist):\n{file_list_str}\n\n"
            f"STATUS REPORT:\n{mission_directive}\n\n"
            "Proceed with the next evolutionary step. Output the FILENAME and CODE."
        )
        
        self.log("AgentPlanner: Query formulated.")
        return system_prompt, user_prompt
