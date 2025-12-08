from pathlib import Path
from tools.decorator import tool

@tool(
    name="read_file",
    description="Read a single text file from a specified path.",
    category="documents"
)
def read_file(file_path: str) -> dict:
    content = Path(file_path).read_text(encoding='utf-8')
    return {"file_path": file_path, "content": content}
