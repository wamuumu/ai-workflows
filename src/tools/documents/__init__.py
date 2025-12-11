from pathlib import Path
from typing import TypedDict, Optional

from tools.decorator import tool

class ListFilesOutput(TypedDict):
    directory: str
    files: list
    count: int

class ReadFileOutput(TypedDict):
    file_path: str
    content: str

class WriteFileOutput(TypedDict):
    file_path: str
    status: str

@tool(
    name="list_files",
    description="List all files in a specified directory with optional extension filter.",
    category="documents"
)
def list_files(directory_path: str, extension: Optional[str] = None) -> ListFilesOutput:
    try:
        dir_path = Path(directory_path)
        if not dir_path.exists():
            return {"error": f"Directory {directory_path} does not exist."}
        
        if not dir_path.is_dir():
            return {"error": f"{directory_path} is not a directory."}
        
        if extension:
            files = [str(f) for f in dir_path.glob(f"*{extension}")]
        else:
            files = [str(f) for f in dir_path.iterdir() if f.is_file()]
        
        return ListFilesOutput(directory=directory_path, files=files, count=len(files))
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="read_file",
    description="Read a single text file from a specified path.",
    category="documents"
)
def read_file(file_path: str) -> ReadFileOutput:
    content = Path(file_path).read_text(encoding='utf-8')
    return ReadFileOutput(file_path=file_path, content=content)

@tool(
    name="write_file",
    description="Write text content to a file. If the file does not exist, it will be created.",
    category="documents"
)
def write_file(file_path: str, content: str) -> WriteFileOutput:
    Path(file_path).write_text(content, encoding='utf-8')
    return WriteFileOutput(file_path=file_path, status="written")