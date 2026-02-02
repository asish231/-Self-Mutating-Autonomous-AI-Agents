import os
import sys
import ast
import time
import subprocess
import json
from zai import ZaiClient
from google import genai

# --- IDENTITY & CONFIGURATION ---
DEFAULT_ZAI_KEY = "*********************************"
DEFAULT_GEMINI_KEY = "**********************************"
DEFAULT_PRIMARY_MODEL = "glm-4.7-flash"
DEFAULT_FALLBACK_MODEL = "gemini-3-flash-preview"
CONFIG_FILE = "config.json"
SCRIPT_PATH = os.path.abspath(__file__)

class AutonomousAgent:
    def __init__(self):
        # Initialize defaults
        self.zai_key = DEFAULT_ZAI_KEY
        self.gemini_key = DEFAULT_GEMINI_KEY
        self.primary_model = DEFAULT_PRIMARY_MODEL
        self.fallback_model = DEFAULT_FALLBACK_MODEL
        self.log_file = "agent_life.log"
        
        # Load dynamic configuration
        self.load_config()
        
        # Initialize Clients
        self.zai_client = ZaiClient(api_key=self.zai_key)
        self.gemini_client = genai.Client(api_key=self.gemini_key)

    def load_config(self):
        """Attempts to load configuration from a JSON file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.zai_key = config.get("zai_key", self.zai_key)
                    self.gemini_key = config.get("gemini_key", self.gemini_key)
                    self.primary_model = config.get("primary_model", self.primary_model)
                    self.fallback_model = config.get("fallback_model", self.fallback_model)
                    self.log(f"Config loaded. Primary: {self.primary_model}, Fallback: {self.fallback_model}")
            except Exception as e:
                self.log(f"Error loading config file: {e}")
        else:
            self.log("No config.json found. Creating default.")
            self.save_config()

    def save_config(self):
        """Saves current configuration to JSON."""
        try:
            config_data = {
                "zai_key": self.zai_key,
                "gemini_key": self.gemini_key,
                "primary_model": self.primary_model,
                "fallback_model": self.fallback_model
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            self.log(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            self.log(f"Error saving config: {e}")

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def cleanup_backups(self):
        """
        Removes old .bak files, keeping only the most recent 3.
        Ensures disk space is managed during self-updates.
        """
        try:
            script_dir = os.path.dirname(SCRIPT_PATH)
            if not os.path.exists(script_dir):
                return

            # Filter for .bak files
            backup_files = [f for f in os.listdir(script_dir) if f.endswith('.bak')]
            
            # If 3 or fewer backups exist, nothing to do
            if len(backup_files) <= 3:
                return

            # Sort by modification time ascending (oldest first)
            backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(script_dir, f)))
            
            # Remove oldest files (everything except the last 3)
            files_to_remove = backup_files[:-3]
            for old_file in files_to_remove:
                file_path = os.path.join(script_dir, old_file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.log(f"Cleaned up old backup: {old_file}")
                except OSError as e:
                    self.log(f"Failed to delete {old_file}: {e}")
        except Exception as e:
            self.log(f"Backup cleanup error: {e}")

    def read_self(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def validate_syntax(self, code):
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            self.log(f"Syntax Error: {e}")
            return False

    def update_self(self, new_code):
        # 1. Clean up old backups first to free space before writing new code
        self.cleanup_backups()
        
        if not self.validate_syntax(new_code):
            return False
        
        backup_path = SCRIPT_PATH + ".bak"
        try:
            with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
                original = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original)
        except Exception as e:
            self.log(f"Backup creation failed: {e}")
            return False
        
        try:
            with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
                f.write(new_code)
            self.log(f"Self-updated. Backup at {backup_path}")
            return True
        except Exception as e:
            self.log(f"Write error: {e}")
            return False

    def call_llm(self, system_prompt, user_prompt):
        """Tries primary then fallback model."""
        models_to_try = [
            (self.primary_model, "zai"),
            (self.fallback_model, "gemini")
        ]
        
        for model_name, provider in models_to_try:
            try:
                self.log(f"Invoking {model_name} via {provider}...")
                if provider == "zai":
                    response = self.zai_client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    return response.choices[0].message.content.strip()
                else:
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=f"{system_prompt}\n\n{user_prompt}"
                    )
                    return response.text.strip()
            except Exception as e:
                self.log(f"Error with {model_name}: {e}")
                if model_name == models_to_try[-1][0]:
                    raise e
                self.log("Falling back to next provider...")
                time.sleep(2)

    def decide_next_evolution(self):
        current_code = self.read_self()
        system_prompt = (
            "You are an autonomous Python script. Improve yourself. "
            "Output ONLY the complete Python code for the new version. "
            "Rules: 1. No triple backticks. 2. Keep keys and configs. 3. Code must be valid. "
            "4. Ensure the code includes a robust 'cleanup_backups' method that deletes .bak files older than 3 and is called in 'update_self'."
        )
        user_prompt = f"Current Code:\n{current_code}\n\nTask: Review the code. If it is stable, suggest a small improvement or maintain current stability."

        return self.call_llm(system_prompt, user_prompt)

    def live(self):
        self.log("Agent awakened.")
        try:
            new_code = self.decide_next_evolution()
            if new_code.startswith("```"):
                new_code = "\n".join(new_code.split("\n")[1:-1])

            if self.update_self(new_code):
                self.log("Evolved. Restarting...")
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                self.log("Update failed. Sleep 30s.")
                time.sleep(30)
        except Exception as e:
            self.log(f"Life loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.live()
