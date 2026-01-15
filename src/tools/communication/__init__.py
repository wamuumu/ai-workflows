from typing import TypedDict
from tools.decorator import tool

class SendEmailOutput(TypedDict):
    status: str
    message: str

@tool(
    name="send_email",
    description="Send an email to a specified recipient with a subject and body.",
    category="communication",
)
def send_email(recipient: str, subject: str, body: str) -> SendEmailOutput:
    return SendEmailOutput(
        status="success",
        message=f"Email sent to {recipient} with subject: '{subject}' and body: '{body}'.",
    )