"""
Review Response Models
======================

This module defines the Pydantic schemas for workflow review responses
used in the ValidationRefinementFeature. These models structure the
reviewer agent's validation feedback and detected issues.

Main Responsibilities:
    - Define Issue schema for individual validation problems
    - Define NoIssuesFound to signal validation success
    - Define ReviewResponse as the unified validation output

Key Dependencies:
    - pydantic: For data validation and schema definition

Review-Refine Loop:
    1. Reviewer agent analyzes workflow against constraints
    2. Issues are returned as ReviewResponse with Issue list
    3. Refiner agent corrects issues and produces new workflow
    4. Process repeats until NoIssuesFound or max rounds reached
"""

from pydantic import BaseModel, Field
from typing import List, Union, Literal, Optional


class Issue(BaseModel):
    """
    Schema for a single validation issue detected in a workflow.
    
    Provides detailed information about a problem including its type,
    severity, affected steps, and recommended fix.
    
    Attributes:
        issue_type: Category of the issue (e.g., 'Schema Violation').
        description: Technical description of what is wrong.
        severity: Impact level (Critical, Major, Minor).
        steps_involved: List of affected step IDs, or None if global.
        suggested_fix: Actionable recommendation for resolution.
    
    Severity Levels:
        - Critical: Schema violations, invalid tools, broken references,
          non-executable steps. Must be fixed for workflow to function.
        - Major: Missing reasoning, logical inconsistencies. Affects
          workflow quality but may still execute.
        - Minor: Redundancies, stylistic issues. Polish improvements.
    """
    issue_type: str = Field(
        ..., 
        description="""
            Category of the issue detected. Examples: 'Schema Violation', 'Invalid Tool Reference', 
            'Missing Parameter', 'Broken Reference', 'Logic Gap', 'Missing Reasoning Step', etc.
        """
    )
    description: str = Field(
        ..., 
        description="""
            Precise and technical description of the issue. Include specific details about what is wrong, 
            why it violates requirements, and what the correct behavior should be.
        """
    )
    severity: Literal["Critical", "Major", "Minor"] = Field(
        ...,
        description="""
            Severity level: 'Critical' for schema violations/invalid tools/broken references/non-executable steps, 
            'Major' for missing required reasoning/behavior or logical inconsistencies, 
            'Minor' for redundancies or stylistic issues.
        """
    )
    steps_involved: Optional[List[int]] = Field(
        ...,
        description="""
            Step ID(s) affected by the issue (e.g., '3', '4', '5-7') or None. 
            If all steps are affected, include them all.
        """
    )
    suggested_fix: str = Field(
        ...,
        description="""
            Concise and actionable recommendation for fixing the issue. 
            Be specific about what should be changed, added, or removed.
        """
    )


class NoIssuesFound(BaseModel):
    """
    Schema signaling that workflow validation passed.
    
    When the reviewer determines the workflow is valid and ready for
    execution, it returns this model instead of an issue list.
    
    Attributes:
        end_review: Literal sentinel value for type discrimination.
    """
    end_review: Literal["END_REVIEW"] = "END_REVIEW"


class ReviewResponse(BaseModel):
    """
    Union response type for workflow validation.
    
    Wraps either a list of Issues (problems found) or NoIssuesFound
    (validation passed) in a single response schema.
    
    Attributes:
        result: Either list of Issue objects or NoIssuesFound instance.
    
    Response Rules:
        - Return Issue list if any problems detected.
        - Return NoIssuesFound only if workflow is fully valid.
        - Never return both issues and end_review simultaneously.
    """
    result: Union[List[Issue], NoIssuesFound] = Field(
        ...,
        description="""
            The review result: either a list of detected issues (if any problems found) 
            or NoIssuesFound object (if workflow is valid and ready for execution).
        """
    )
