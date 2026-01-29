"""
Workflow Models Package
=======================

This package provides Pydantic model definitions for workflow representations
in the AI-Workflows framework. Two workflow types are supported:

    - LinearWorkflow: Sequential execution without branching
    - StructuredWorkflow: Conditional execution with branching transitions

Usage:
    from models.workflows import LinearWorkflow, StructuredWorkflow
"""

from models.workflows.linear_workflow import LinearWorkflow
from models.workflows.structured_workflow import StructuredWorkflow