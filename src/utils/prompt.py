"""
Prompt Utilities Module
=======================

This module provides centralized prompt management for the AI Workflows framework.
Prompts are loaded from filesystem files and cached for efficient repeated access.

Prompt Types:
    - System Prompts: Markdown (.md) files defining LLM behavior and instructions.
      Located in ``src/prompts/system/``.
    - User Prompts: JSON files containing different prompt iterations.
      Located in ``src/prompts/user/``.

Key Features:
    - Lazy loading with caching for performance
    - Filename-based keying (e.g., ``workflow_generation.md`` → key ``workflow_generation``)
    - Dynamic prompt injection for adding context

Usage Example:
    >>> prompt = PromptUtils.get_system_prompt("workflow_generation")
    >>> enriched = PromptUtils.inject(prompt, tools_description="...")
"""

import os
import json

from pathlib import Path

# Compute prompt directory paths relative to module location
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_PROMPTS_DIR = os.path.join(ROOT, "prompts", "system")
USER_PROMPTS_DIR = os.path.join(ROOT, "prompts", "user")


class PromptUtils:
    """
    Utility class for managing and accessing prompt templates.
    
    Provides lazy-loaded access to system and user prompts stored
    as files. Prompts are cached after first load for efficiency.
    
    Class Attributes:
        _system_prompts: Cache of loaded system prompts (name → content).
        _user_prompts: Cache of loaded user prompts (name → JSON data).
    """

    _system_prompts: dict[str, str] = {}
    _user_prompts: dict[str, dict[str, str]] = {}

    @classmethod
    def _load_system_prompts(cls, directory: Path) -> dict[str, str]:
        """
        Load all Markdown system prompt files from a directory.
        
        Args:
            directory: Path to directory containing .md files.
            
        Returns:
            Dict mapping filename stems to file contents.
            
        Raises:
            FileNotFoundError: If directory does not exist.
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        prompts = {}
        for file in directory.glob("*.md"):
            key = file.stem
            with open(file, "r", encoding="utf-8") as f:
                prompts[key] = f.read()
        return prompts

    @classmethod
    def _load_user_prompts(cls, directory: Path) -> dict[str, dict[str, str]]:
        """
        Load all JSON prompt files from a directory.
        
        Args:
            directory: Path to directory containing .json files.
            
        Returns:
            Dict mapping filename stems to parsed JSON data.
            
        Raises:
            FileNotFoundError: If directory does not exist.
        """
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
        """
        Ensure prompts are loaded from disk.
        
        Lazy initialization - only loads files on first access.
        """
        if not cls._system_prompts:
            cls._system_prompts = cls._load_system_prompts(Path(SYSTEM_PROMPTS_DIR))
        if not cls._user_prompts:
            cls._user_prompts = cls._load_user_prompts(Path(USER_PROMPTS_DIR))
    
    @classmethod
    def get_system_prompt(cls, name: str) -> str:
        """
        Retrieve a system prompt by name.
        
        Args:
            name: Prompt name (filename without .md extension).
            
        Returns:
            The prompt content as a string.
            
        Raises:
            KeyError: If prompt name not found.
        """
        cls._ensure_loaded()
        if name not in cls._system_prompts:
            raise KeyError(f"System prompt not found: {name}")
        return cls._system_prompts[name]

    @classmethod
    def get_user_prompts(cls, name: str) -> dict[str, str]:
        """
        Retrieve user prompts by name.
        
        Args:
            name: Prompt collection name (filename without .json extension).
            
        Returns:
            The parsed JSON data (typically a dict of prompt templates).
            
        Raises:
            KeyError: If prompt collection not found.
        """
        cls._ensure_loaded()
        if name not in cls._user_prompts:
            raise KeyError(f"User prompts not found: {name}")
        return cls._user_prompts[name]

    @classmethod
    def list_system_prompts(cls) -> list[str]:
        """
        List available system prompt names.
        
        Returns:
            List of system prompt names (keys).
        """
        cls._ensure_loaded()
        return list(cls._system_prompts.keys())

    @classmethod
    def list_user_prompts(cls) -> list[str]:
        """
        List available user prompt collection names.
        
        Returns:
            List of user prompt collection names (keys).
        """
        cls._ensure_loaded()
        return list(cls._user_prompts.keys())
    
    @classmethod
    def inject(cls, prompt: str, *args, **kwargs) -> str:
        """
        Inject additional content into a prompt.
        
        Appends positional arguments as lines and keyword arguments
        as ``key: value`` pairs. Used to add dynamic context to
        base prompts before sending to LLM.
        
        Args:
            prompt: Base prompt string to extend.
            *args: Additional content to append as lines.
            **kwargs: Key-value pairs to append as ``key: value``.
            
        Returns:
            The extended prompt string.
            
        Example:
            >>> base = "Generate a workflow for:"
            >>> PromptUtils.inject(base, user_task="book a flight")
        """

        for arg in args:
            prompt += f"\n{arg}"
            
        for key, value in kwargs.items():
            prompt += f"\n{key}: {value}"
        return prompt