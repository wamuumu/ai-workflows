from pydantic import BaseModel, Field
from typing import List, Union, Literal, Optional

class Issue(BaseModel):
    """A detected issue in a workflow."""
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
    """Indicates that the workflow passed all validation checks."""
    end_review: Literal["END_REVIEW"] = "END_REVIEW"

class ReviewResponse(BaseModel):
    """A workflow validation review response.
    
    Response Rules:
    - Never return both issues and end_review in the same response
    """
    result: Union[List[Issue], NoIssuesFound] = Field(
        ...,
        description="""
            The review result: either a list of detected issues (if any problems found) 
            or NoIssuesFound object (if workflow is valid and ready for execution).
        """
    )
