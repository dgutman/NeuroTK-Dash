import cv2 as cv
import numpy as np


def imread(fp: str, fmt: str = 'rgb', grayscale: bool = False) -> np.ndarray:
    """
    Read image file*.

    * Only supports RGB images currently, in the future we will look add 
    support for RGBA and grayscale images.
    
    Args:
        fp (str): Filepath to image.
        fmt (str): Format to read image as: 'rgb', 'bgr', 'gray'.
        grayscale (bool): Will be deprecated in the future, similar behavior can
            be achieved by setting format to 'gray'. Read image as grayscale.
    
    Returns:
        (numpy.ndarray) Image as numpy array.
    
    """
    assert fmt in ('rgb', 'bgr', 'gray'), "fmt must be 'rgb', 'bgr' or 'gray'."
    
    if grayscale:
        return cv.imread(fp, cv.IMREAD_GRAYSCALE)
    
    img = cv.imread(fp)
    
    if fmt == 'rgb':
        return cv.cvtColor(img, cv.COLOR_BGR2RGB)
    elif fmt == 'gray':
        return cv.cvtColor(img, cv.IMREAD_GRAYSCALE)
    else:
        return img
