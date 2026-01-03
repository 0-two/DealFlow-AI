"""
Helper utility functions
"""
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path


def format_timestamp(timestamp: datetime = None) -> str:
    """
    Format timestamp as ISO string
    
    Args:
        timestamp: Datetime object (defaults to now)
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.isoformat()


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_get(dictionary: Dict[str, Any], *keys, default: Any = None) -> Any:
    """
    Safely get nested dictionary values
    
    Args:
        dictionary: Dictionary to search
        *keys: Keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at the nested key path or default
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result if result is not None else default


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

