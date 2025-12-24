import os
import json

from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_PROMPTS_DIR = os.path.join(ROOT, "prompts", "system")
USER_PROMPTS_DIR = os.path.join(ROOT, "prompts", "user")

class PromptUtils:
    """Utility class for managing prompts."""

    _system_prompts: dict[str, str] = {}
    _user_prompts: dict[str, str] = {}

    @classmethod
    def _load_system_prompts(cls, directory: Path) -> dict[str, str]:
        """Load all .md files in a directory into a dictionary."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        prompts = {}
        for file in directory.glob("*.md"):
            key = file.stem
            with open(file, "r", encoding="utf-8") as f:
                prompts[key] = f.read()
        return prompts

    @classmethod
    def _load_user_prompts(cls, directory: Path) -> dict[str, str]:
        """Load all .json files in a directory into a dictionary."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        prompts = {}
        for file in directory.glob("*.json"):
            key = file.stem
            with open(file, "r", encoding="utf-8") as f:
                prompts[key] = json.load(f)
        return prompts

    @classmethod
    def _ensure_loaded(cls):
        """Load prompts if not already loaded."""
        if not cls._system_prompts:
            cls._system_prompts = cls._load_system_prompts(Path(SYSTEM_PROMPTS_DIR))
        if not cls._user_prompts:
            cls._user_prompts = cls._load_user_prompts(Path(USER_PROMPTS_DIR))
    
    @classmethod
    def get_system_prompt(cls, name: str) -> str:
        cls._ensure_loaded()
        if name not in cls._system_prompts:
            raise KeyError(f"System prompt not found: {name}")
        return cls._system_prompts[name]

    @classmethod
    def get_user_prompts(cls, name: str) -> str:
        cls._ensure_loaded()
        if name not in cls._user_prompts:
            raise KeyError(f"User prompts not found: {name}")
        return cls._user_prompts[name]

    @classmethod
    def list_system_prompts(cls) -> list[str]:
        cls._ensure_loaded()
        return list(cls._system_prompts.keys())

    @classmethod
    def list_user_prompts(cls) -> list[str]:
        cls._ensure_loaded()
        return list(cls._user_prompts.keys())
    
    @classmethod
    def inject(cls, prompt: str, *args, **kwargs) -> str:
        """Inject arguments into the system prompt ONLY."""

        for arg in args:
            prompt += f"\n{arg}"
            
        for key, value in kwargs.items():
            prompt += f"\n{key}: {value}"
        return prompt