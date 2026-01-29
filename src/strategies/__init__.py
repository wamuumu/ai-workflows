"""
Strategies Package
==================

This package contains workflow generation strategies implementing different
approaches to creating AI workflows from user prompts.

Available Strategies:
    - MonolithicStrategy: Single-shot complete workflow generation
    - IncrementalStrategy: Iterative step-by-step workflow building
    - BottomUpStrategy: Multi-phase analysis-based workflow construction

Usage Example:
    >>> from strategies import MonolithicStrategy
    >>> strategy = MonolithicStrategy()
    >>> workflow = strategy.generate(context, max_retries=3, debug=False)
"""

from strategies.monolithic import MonolithicStrategy
from strategies.incremental import IncrementalStrategy
from strategies.bottom import BottomUpStrategy