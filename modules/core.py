import json
import time
import os
import sys
from typing import Callable, Any

# --- DEPENDENCIES ---
try:
    from google import genai
    from zai import ZaiClient
except ImportError:
    # This bootstrap module should not try to install dependencies,
    # as GenesisKernel is responsible for that.
    # We assume dependencies are already handled by evolve_agent.py's initial check.
    pass

class ModelClientManager:
    """
    Manages interactions with various Language Model (LLM) providers,
    implementing a failover strategy based on configured primary,
    secondary, and fallback models.
    """
    def __init__(self, config: dict, logger: Callable[[str], None]):
        """
        Initializes the ModelClientManager with API configurations and a logging function.

        Args:
            config (dict): A dictionary containing 'api_keys' and 'models' configurations.
            logger (Callable[[str], None]): A function to use for logging messages.
        """
        self.config = config
        self.log = logger
        self.keys = config.get("api_keys", {})
        self.models = config.get("models", {})
        
        # State
        self.failed_attempts = 0
        self.current_provider = "primary" # primary, secondary, fallback
        self.permanent_fallback = False # If switched to ZAI, stay there

        # Init Clients (only if keys are present)
        self.zai = ZaiClient(api_key=self.keys.get("zai")) if self.keys.get("zai") else None
        self.gemini_key = self.keys.get("gemini")

        if not self.zai:
            self.log("Warning: ZAI API key not found. ZAI provider disabled.")
        if not self.gemini_key:
            self.log("Warning: Gemini API key not found. Gemini provider disabled.")
            if self.zai: # If Gemini is disabled, force ZAI as primary if available
                self.current_provider = "fallback"
                self.permanent_fallback = True
                self.log("Gemini keys missing, defaulting to ZAI as primary.")
            else:
                pass # Check openrouter later

        self.openrouter_key = self.keys.get("openrouter")
        if not self.openrouter_key:
            self.log("Warning: OpenRouter API key not found.")

    def call(self, system_prompt: str, user_prompt: str) -> str:
        """
        Calls the appropriate LLM based on the current provider strategy.
        Implements smart switching logic and retry mechanisms.
        """
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Priority 1: Primary (Gemini)
        if not self.permanent_fallback and self.current_provider == "primary" and self.gemini_key:
            try:
                # Use retry wrapper internally or just try once here?
                # The original code had retry loop here.
                return self._call_gemini(self.models.get("primary"), full_prompt)
            except Exception as e:
                self.log(f"Primary ({self.models.get('primary', 'N/A')}) failed: {type(e).__name__}: {e}")
                self.failed_attempts += 1
                if self.failed_attempts >= self.config.get("provider_switch_threshold", 2):
                    self.current_provider = "secondary"
                    self.failed_attempts = 0
                    self.log(f"Switching to secondary provider: {self.current_provider}")
                else:
                    self.log(f"Retrying primary...")
                    time.sleep(2)
                    return self.call(system_prompt, user_prompt)

        # Priority 2: Secondary (OpenRouter)
        # Note: Original code had Gemini Secondary. We are replacing Secondary with OpenRouter as per user request.
        # "after gemini trial use the openrouter"
        if not self.permanent_fallback and self.current_provider == "secondary":
            if self.openrouter_key:
                try:
                    return self._call_openrouter(self.models.get("secondary"), system_prompt, user_prompt)
                except Exception as e:
                    self.log(f"Secondary (OpenRouter) failed: {type(e).__name__}: {e}")
                    self.failed_attempts += 1
                    if self.failed_attempts >= self.config.get("provider_switch_threshold", 2):
                        self.current_provider = "fallback"
                        self.permanent_fallback = True
                        self.log("Switched to PERMANENT FALLBACK (ZAI).")
                        self.failed_attempts = 0
                    else:
                        time.sleep(2)
                        return self.call(system_prompt, user_prompt)
            else:
                self.log("OpenRouter key missing, skipping to Fallback.")
                self.current_provider = "fallback"
                self.permanent_fallback = True

        # Priority 3: Fallback (ZAI)
        if self.zai:
            try:
                return self._call_zai(self.models.get("fallback"), system_prompt, user_prompt)
            except Exception as e:
                self.log(f"Fallback (ZAI) failed: {e}")
                raise Exception("All LLM providers failed.")
        else:
            raise Exception("No active LLM providers configured.")

    def _call_openrouter(self, model_name: str, system: str, user: str) -> str:
        """Internal method to call OpenRouter API."""
        if not self.openrouter_key:
             raise ValueError("OpenRouter API Key missing")
        
        self.log(f"Calling OpenRouter: {model_name}")
        
        # Use simple Requests if available (standard in Python environment usually)
        # Fallback to urllib if requests is missing (to avoid dependency hell)
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://genesis-kernel.local", # Required by OpenRouter
            "X-Title": "Genesis Kernel"
        }
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        }
        
        # Try urllib for minimal dependencies
        import urllib.request
        import urllib.error
        
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'choices' in result and len(result['choices']) > 0:
                    return self._clean_response(result['choices'][0]['message']['content'])
                else:
                    raise Exception(f"OpenRouter empty response: {result}")
        except Exception as e:
            # Try requests if urllib failed (debug)
            raise e

    def _clean_response(self, text: str) -> str:
        """
        Aggressively cleans LLM output to extract only the code/content.
        Removes markdown backticks, 'thought' traces, and extraneous conversational text.
        """
        if not text: return ""
        
        # 1. Strip Markdown Code Blocks
        if "```" in text:
            import re
            match = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1)
            else:
                text = text.replace("```python", "").replace("```", "")
        
        # 2. If NO backticks, try to rescue the code using Regex
        else:
            # Look for the first line starting with standard python keywords
            import re
            # Multiline regex to find the start of code
            match = re.search(r"^(import|from|class|def|FILENAME:)\s+.*", text, re.MULTILINE | re.DOTALL)
            if match:
                # We found the start index
                start_index = match.start()
                text = text[start_index:]
            else:
                 # Last resort: Try to parse lines again manually if regex fails
                 lines = text.split('\n')
                 for i, line in enumerate(lines):
                     if line.strip().startswith(("import ", "from ", "class ", "def ", "FILENAME:")):
                         text = "\n".join(lines[i:])
                         break

        # 3. Trim whitespace
        text = text.strip()
        return text


    def _call_gemini(self, model_name: str, content: str) -> str:
        """Internal method to call Google Gemini API."""
        if not self.gemini_key:
            raise ValueError("Gemini API key is not configured.")
        if not model_name:
            raise ValueError("Gemini model name not specified in config.")

        self.log(f"Calling Google Gemini: {model_name}")
        client = genai.Client(api_key=self.gemini_key)
        
        # Using generate_content for flexibility, assumes 'contents' can take a string
        # as a shorthand for [{'role': 'user', 'parts': [content]}]
        response = client.models.generate_content(
            model=model_name,
            contents=content
        )
        # Assuming the response object has a 'text' attribute for the content
        if hasattr(response, 'text') and response.text:
             return self._clean_response(response.text)
        elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             # Fallback for structured content
             text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')]
             combined_text = "".join(text_parts).strip()
             return self._clean_response(combined_text)
        else:
             raise Exception("Gemini returned empty or unstructured response (possible safety block).")

    def _call_zai(self, model_name: str, system: str, user: str) -> str:
        """Internal method to call Z.AI API."""
        if not self.zai:
            raise ValueError("ZAI client is not initialized (API key missing?).")
        if not model_name:
            raise ValueError("ZAI model name not specified in config.")

        self.log(f"Calling Z.AI: {model_name}")
        response = self.zai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        return self._clean_response(response.choices[0].message.content)

# Other core functionalities or common utilities can be added here later.
# For now, this establishes the foundational LLM communication manager.