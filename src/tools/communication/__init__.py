"""
Communication Tools Module
==========================

This module provides communication-related tools for sending
messages and notifications.

Main Responsibilities:
    - Send email notifications
    - (Future: SMS, push notifications, etc.)

Key Dependencies:
    - tools.decorator: For @tool registration

Note:
    The current implementation is a stub that simulates email sending.
    Production use would require integration with an actual email
    service (SMTP, SendGrid, etc.).
"""

from typing import TypedDict
from tools.decorator import tool


class SendEmailOutput(TypedDict):
    """
    Structured output for email sending.
    
    Attributes:
        status: Operation status ("success" or "error").
        message: Descriptive message about the operation.
    """
    status: str
    message: str


@tool(
    name="send_email",
    description="Send an email to a specified recipient with a subject and body.",
    category="communication",
)
def send_email(recipient: str, subject: str, body: str) -> SendEmailOutput:
    """
    Send an email (simulated).
    
    This is a stub implementation that simulates sending an email.
    In production, this would integrate with an email service.
    
    Args:
        recipient: Email address of the recipient.
        subject: Email subject line.
        body: Email body content.
        
    Returns:
        SendEmailOutput with status and confirmation message.
    """
    return SendEmailOutput(
        status="success",
        message=f"Email sent to {recipient} with subject: '{subject}' and body: '{body}'.",
    )