"""
Strategy Base Module
====================

This module defines the abstract base class for all workflow generation
strategies, establishing the interface contract for strategy implementations.

Main Responsibilities:
    - Define abstract interface for workflow generation
    - Provide common initialization logic for strategy parameters
    - Enable strategy pattern for flexible workflow generation approaches

Design Pattern:
    Implements the Strategy design pattern, allowing different algorithms
    for workflow generation to be selected at runtime without modifying
    the orchestrator that uses them.

Key Dependencies:
    - abc: For abstract base class definition
    - pydantic: For BaseModel type hint in return values
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel


class StrategyBase(ABC):
    """
    Abstract base class for workflow generation strategies.
    
    Defines the interface that all generation strategies must implement.
    Each strategy encapsulates a different approach to converting user
    prompts into executable workflows.
    
    Attributes:
        **kwargs: Strategy-specific configuration parameters stored
            as instance attributes.
    
    Subclasses:
        - MonolithicStrategy: One-shot complete generation
        - IncrementalStrategy: Iterative step-by-step building
        - BottomUpStrategy: Multi-phase analysis-driven construction
    """

    def __init__(self, **kwargs):
        """
        Initialize strategy with configuration parameters.
        
        Dynamically sets instance attributes from keyword arguments,
        allowing flexible configuration for different strategy types.
        
        Args:
            **kwargs: Strategy-specific parameters (e.g., batch_size,
                max_rounds) stored as instance attributes.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @abstractmethod
    def generate(self, context, max_retries: int, debug: bool) -> BaseModel:
        """
        Generate a workflow from the provided context.
        
        Abstract method that must be implemented by concrete strategies.
        Each implementation defines its own approach to workflow creation.
        
        Args:
            context: Orchestrator context containing prompt, agents, and
                tools for workflow generation.
            max_retries: Maximum retry attempts for LLM API calls.
            debug: Whether to enable debug output during generation.
            
        Returns:
            Generated workflow as a Pydantic BaseModel instance
            (typically LinearWorkflow or StructuredWorkflow).
            
        Raises:
            NotImplementedError: If called on StrategyBase directly.
        """
        pass