# 🧠 Autonomous Agent Architecture & Specifications

**Version:** 0.1 (Experimental)  
**Researcher:** Asish Kumar Sharma | SafarNow Innovation Developments

---

## 1. Core Identity

The **Evolve Agent** is a recursively self-improving Python program. Unlike traditional software that remains static until a developer pushes an update, this agent is designed to be **fluid**. It treats its own source code as mutable memory, allowing it to adapt its architecture, logic, and capabilities in real-time based on high-level directives.

### The Biological Loop

The agent operates on a continuous feedback loop that mimics biological evolution:

1.  **Awakening (`__init__`)**: The agent initializes, establishes its identity, and connects to its cognitive providers.
2.  **Introspection (`read_self`)**: It reads its current source code into memory.
3.  **Cognition (`decide_next_evolution`)**: It consults an LLM to analyze its structure and determine the next logical improvement.
4.  **Mutation (`update_self`)**: It rewrites its source file with the new code.
5.  **Rebirth (`os.execv`)**: It terminates the current process and instantly spawns a new instance of the updated code.

---

## 2. Cognitive Architecture (The "Dual-Brain")

The agent possesses a hybrid cognitive system ensuring high availability and reasoning diversity.

### Primary Cortex: ZAI (GLM-4.7-Flash)

- **Role:** The main driver for logic, coding, and architectural decision-making.
- **Trigger:** Called first for every evolutionary task.

### Sentinel Cortex: Google Gemini (Gemini-3-Flash-Preview)

- **Role:** The fail-safe backup.
- **Trigger:** Activates automatically if the primary cortex fails due to:
  - Network timeouts.
  - Rate limiting errors.
  - API outages.
- **Behavior:** The agent logs the failure, switches providers seamlessly, and retries the task without crashing.

---

## 3. Capabilities & Functions

### A. Self-Editing (Refactoring)

The agent has full write access to its own source file (`evolve_agent.py`). It can:

- Add new imports and libraries.
- Create new classes and methods.
- Refactor existing logic for efficiency.
- Modify its own system prompts to change its personality or goals.

### B. Genetic Safety System

To prevent "lethal mutations" (code that breaks the agent permanently), it implements a rigid safety protocol:

1.  **Syntax Validation:** Before writing any new code to disk, the agent runs `ast.parse()` on the generated string. If the syntax is invalid (e.g., missing colons, indentation errors), the update is rejected.
2.  **Snapshotting:** Before every update, the current working version is saved as a `.bak` file.
3.  **Auto-Cleanup:** The agent monitors its environment and automatically deletes old backups, maintaining a rolling window of the **3 most recent versions** to preserve disk space.

### C. persistent Memory

The agent maintains continuity across lifecycles using external storage:

- **`config.json`**: Stores sensitive credentials (API keys) and model preferences. This allows the agent to update its code without hardcoding secrets or losing its configuration.
- **`agent_life.log`**: A chronological journal of every thought, error, evolutionary step, and restart event.

---

## 4. Technical Specifications

| Feature               | Implementation Details                         |
| :-------------------- | :--------------------------------------------- |
| **Language**          | Python 3.x                                     |
| **Execution Model**   | Single-process, recursive restart (`os.execv`) |
| **Communication**     | REST API (ZAI Client & Google GenAI SDK)       |
| **Failover Strategy** | Try/Catch block with immediate provider switch |
| **Disk Operations**   | Standard `os` and `shutil` libraries           |
| **Safety**            | Abstract Syntax Tree (AST) validation          |

---

## 5. Potential & Trajectory

While currently a single-file organism, the agent's architecture supports unrestricted growth. Potential future evolutionary paths include:

- **Mitosis:** Splitting its code into multiple modules (`perception.py`, `action.py`, `memory.py`) to handle complexity.
- **Sensory Expansion:** Writing code to access the internet via `requests` or `selenium` to gather data.
- **Replication:** Copying itself to other directories to run parallel experiments.
- **GUI Development:** Generating a frontend interface to visualize its own internal state.

> **Note:** The agent is confined only by the permissions of the user and the prompt directives given to it. It is an open-ended engine for autonomous software development.
