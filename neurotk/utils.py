"""Utility functions."""
from typing import List
from typing import List

from os import makedirs
from os.path import basename, splitext


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


def contours_to_points(contours: List) -> List:
    """Convert a list of opencv contours (i.e. contour shape is 
    (num_points, 1, 2) with x, y order) to a list of x,y point in format 
    ready to push as DSA annotations. This form is a list of lists with 
    [x, y, z] format where the z is always 0.
    
    Args:
        contours: List of numpy arrays in opencv contour format

    Returns:
        Points in DSA format.
    
    """
    points = []
    
    for contour in contours:
        points.append([
            [float(pt[0][0]), float(pt[0][1]), 0] for pt in contour
        ])
        
    return points


def get_filename(fp: str, prune_ext: bool = True) -> str:
    """Get the filename of a filepath.

    Args:
        fp: Filepath.
        prune_ext: Remove extension.
    
    Returns:
        Filename.

    """
    fn = basename(fp)

    if prune_ext:
        fn = splitext(fn)[0]

    return fn
