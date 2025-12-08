from pathlib import Path

from tools.decorator import tool

@tool(
    name="save_file",
    description="Save text content to a specified file path.",
    category="documents"
)
def save_file(file_path: str, content: str) -> dict:
    Path(file_path).write_text(content, encoding='utf-8')
    return {"file_path": file_path, "status": "saved"}