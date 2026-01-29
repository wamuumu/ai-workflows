"""
Documents Tools Module
======================

This module provides tools for file system operations including
listing, reading, and writing text files.

Main Responsibilities:
    - List files in directories with optional filtering
    - Read text file contents
    - Write content to text files

Key Dependencies:
    - pathlib: Path manipulation and file operations
    - tools.decorator: For @tool registration

Security Note:
    These tools operate on the local file system. Ensure proper
    access controls and input validation in production use.
"""

from pathlib import Path
from typing import TypedDict, Optional

from tools.decorator import tool


class ListFilesOutput(TypedDict):
    """
    Structured output for directory listing.
    
    Attributes:
        directory: The path of the listed directory.
        files: List of file paths in the directory.
        count: Number of files found.
    """
    directory: str
    files: list
    count: int


class ReadFileOutput(TypedDict):
    """
    Structured output for file reading.
    
    Attributes:
        file_path: The path of the file that was read.
        content: The text content of the file.
    """
    file_path: str
    content: str


class WriteFileOutput(TypedDict):
    """
    Structured output for file writing.
    
    Attributes:
        file_path: The path of the file that was written.
        status: Operation status ("written" on success).
    """
    file_path: str
    status: str


@tool(
    name="list_files",
    description="List all files in a specified directory with optional extension filter.",
    category="documents"
)
def list_files(directory_path: str, extension: Optional[str] = None) -> ListFilesOutput:
    """
    List files in a directory.
    
    Retrieves all files in the specified directory, optionally
    filtered by file extension.
    
    Args:
        directory_path: Path to the directory to list.
        extension: Optional file extension filter (e.g., ".txt").
        
    Returns:
        ListFilesOutput with directory path, file list, and count.
        Returns error dict if directory doesn't exist or isn't valid.
    """
    try:
        dir_path = Path(directory_path)
        
        # Validate directory exists
        if not dir_path.exists():
            return {"error": f"Directory {directory_path} does not exist."}
        
        # Validate path is a directory
        if not dir_path.is_dir():
            return {"error": f"{directory_path} is not a directory."}
        
        # List files with optional extension filter
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
    """
    Read text content from a file.
    
    Reads the entire contents of a text file using UTF-8 encoding.
    
    Args:
        file_path: Path to the file to read.
        
    Returns:
        ReadFileOutput with file path and content.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
        UnicodeDecodeError: If file isn't valid UTF-8.
    """
    content = Path(file_path).read_text(encoding='utf-8')
    return ReadFileOutput(file_path=file_path, content=content)


@tool(
    name="write_file",
    description="Write text content to a file. If the file does not exist, it will be created.",
    category="documents"
)
def write_file(file_path: str, content: str) -> WriteFileOutput:
    """
    Write text content to a file.
    
    Creates the file and parent directories if they don't exist.
    Overwrites existing file content.
    
    Args:
        file_path: Path where file should be written.
        content: Text content to write.
        
    Returns:
        WriteFileOutput with file path and status.
    """
    # Ensure parent directory exists
    if not Path(file_path).parent.exists():
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write content to file
    Path(file_path).write_text(content, encoding='utf-8')
    return WriteFileOutput(file_path=file_path, status="written")