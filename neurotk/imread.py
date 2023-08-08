import cv2 as cv
import numpy as np

def imread(fp: str) -> np.array:
    """
    Read image file*.

    * Only supports RGB images currently, in the future we will look add 
    support for RGBA and grayscale images.
    
    Args:
        fp: Filepath to image.
    
    Returns:
        Image as numpy array.
    
    """
    return cv.cvtColor(cv.imread(fp), cv.COLOR_BGR2RGB)
