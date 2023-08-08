import cv2 as cv
import numpy as np


def imwrite(fp: str, img: np.array, grayscale: bool = False):
    """Write image to file.
    
    Args:
        fp: Filepath to save image.
        img: Image to save.
        grayscale: True to save image as a grayscale image, otherwise it is
            saved as an RGB image.
    
    """
    if grayscale:
        cv.imwrite(fp, img)
    else:
        cv.imwrite(fp, cv.cvtColor(img, cv.COLOR_RGB2BGR))
