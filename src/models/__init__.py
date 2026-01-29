"""
Models Package
==============

This package defines Pydantic data models used throughout the AI Workflows
framework for structured data validation and serialization.

Sub-packages:
    workflows: Workflow structure models (LinearWorkflow, StructuredWorkflow)
        defining the output format for workflow generation.
    responses: LLM response models for various interaction patterns
        (execution, review, bottom-up analysis, etc.).

Design Philosophy:
    All models use Pydantic BaseModel for:
        - Automatic validation of LLM outputs
        - JSON serialization/deserialization
        - Type hints and documentation
        - Schema generation for structured output prompts
"""