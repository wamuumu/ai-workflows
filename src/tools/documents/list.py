from pathlib import Path
from typing import Optional
from tools.decorator import tool

@tool(
    name="list_files",
    description="List all files in a specified directory with optional extension filter.",
    category="documents"
)
def list_files(directory_path: str, extension: Optional[str] = None) -> dict:
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
        
        return {"directory": directory_path, "files": files, "count": len(files)}
    except Exception as e:
        return {"error": str(e)}