"""
Utils Package
=============

This package provides utility modules for the AI Workflows framework,
supporting logging, metrics, prompt management, and workflow persistence.

Available Modules:
    logger: Centralized logging infrastructure with timestamped file output.
    metric: Comprehensive evaluation and efficiency metrics for workflows.
    prompt: Prompt template management and dynamic injection.
    workflow: Workflow serialization, loading, and visualization utilities.

Usage:
    These utilities are typically used internally by orchestrators and
    strategies, but can be imported directly for custom integrations.

Example:
    >>> from utils.logger import LoggerUtils
    >>> from utils.metric import MetricUtils
    >>> from utils.prompt import PromptUtils
    >>> from utils.workflow import WorkflowUtils
"""