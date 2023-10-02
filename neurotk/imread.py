import cv2 as cv
import numpy as np


def imread(fp: str, grayscale: bool = False) -> np.ndarray:
    """
    Read image file*.

    * Only supports RGB images currently, in the future we will look add 
    support for RGBA and grayscale images.
    
    Args:
        fp: Filepath to image.
        grayscale: Read image as grayscale.
    
    Returns:
        Image as numpy array.
    
    """
    if grayscale:
        return cv.imread(fp, cv.IMREAD_GRAYSCALE)
    else:
        return cv.cvtColor(cv.imread(fp), cv.COLOR_BGR2RGB)
