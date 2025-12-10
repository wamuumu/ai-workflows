from tools.decorator import tool

@tool(
    name="send_email",
    description="Send an email to a specified recipient with a subject and body.",
    category="communication",
)
def send_email(recipient: str, subject: str, body: str) -> dict:
    return {
        "status": "success",
        "message": f"Email sent to {recipient} with subject '{subject}'.",
        "body": body
    }