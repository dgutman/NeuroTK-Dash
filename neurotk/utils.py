from typing import List
from os import makedirs


def create_dirs(dirs: List[str], exist_ok: bool = True):
    """Create multiple directories.
    
    Args:
        dirs: List of directories.
        exist_ok: If False raise error if directory already exists.
        
    """
    for d in dirs:
        makedirs(d, exist_ok=exist_ok)
