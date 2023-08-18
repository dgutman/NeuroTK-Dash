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


def replace_last_occurence(string: str, old: str, new: str, 
                           required: bool = False) -> str:
    """Replace the last occurence of a substring in a string.
    
    Source: "https://www.tutorialspoint.com/How-to-replace-the-last-occurrence-of-an-expression-in-a-string-in-Python"
    
    Args:
        string: Input string.
        old: Substring to replace.
        new: New substring to use.
        required: Old substring must be present in the string.

    Returns:
        Output string.

    Raises:
        ValueError if old substring not in input string and required is set 
            to True.
    
    """
    if required:
        if old not in string:
            raise ValueError(f'Old substring \"{old}\" not in \"{string}\".'
                             ' To ignore such errors set \"required\" '
                             'parameter to False.')
            
    return new.join(string.rsplit(old, 1))
