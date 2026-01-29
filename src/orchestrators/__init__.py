"""
Orchestrators Package
=====================

This package provides workflow orchestration capabilities for the AI Workflows
framework. Orchestrators coordinate the entire workflow lifecycle from
generation through execution.

The primary component is the ConfigurableOrchestrator, which:
    - Manages agent pools for different workflow phases
    - Applies pre-generation and post-generation features
    - Coordinates strategy-based workflow generation
    - Handles workflow execution with tool invocation

Available Classes:
    ConfigurableOrchestrator: Main orchestration engine for workflow
        generation and execution.
"""

from orchestrators.base import ConfigurableOrchestrator