"""
Features Package
================

This package provides enhancement features that augment the workflow generation
pipeline. Features operate in either "pre" phase (before generation) or "post"
phase (after generation).

Available Features:
    - ChatClarificationFeature (pre): Interactive clarification via chat
    - RefinementFeature (post): Single-pass workflow improvement
    - ValidationRefinementFeature (post): Iterative review and refinement

Usage:
    from features import ChatClarificationFeature, RefinementFeature
    
    features = [ChatClarificationFeature(), RefinementFeature()]
    orchestrator = ConfigurableOrchestrator(strategy, tools, features=features)
"""

from features.clarification import ChatClarificationFeature
from features.refinement import RefinementFeature
from features.validation_refiniment import ValidationRefinementFeature