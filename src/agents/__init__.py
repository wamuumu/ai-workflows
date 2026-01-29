"""
Agents Package
==============

This package provides LLM agent implementations for the AI-Workflows framework.
Each agent wraps a specific LLM provider's API and implements the common
AgentBase interface defined in the base module.

Available Agents:
    - GeminiAgent: Google's Gemini models (2.5 Flash, 2.5 Flash Lite)
    - CerebrasAgent: Cerebras Cloud models (GPT-OSS, Llama 3.3)

Usage:
    from agents.google import GeminiAgent, GeminiModel
    from agents.cerebras import CerebrasAgent, CerebrasModel
    
    # Initialize an agent
    agent = GeminiAgent(GeminiModel.GEMINI_2_5_FLASH)
    
    # Generate content
    response = agent.generate_content(system_prompt, user_prompt)
"""
