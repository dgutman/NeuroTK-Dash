# Utility functions when working with OpenCV style contours.
from typing import List
import numpy as np


def get_contours_from_annotations(
    annotation_docs: List[dict]
) -> List[np.array]:
    """Extract polyline annotation elements as contours-like arrays from 
    a list of annotaiton documents.
    
    Args:
        Annotation documents.

    Returns:
        
    """
    contours = []

    for doc in annotation_docs:
        for element in doc['annotation']['elements']:
            if element['type'] == 'polyline':
                contour = []

                for xyz in element['points']:
                    contour.append([int(xyz[0]), int(xyz[1])])

                contour = np.array(contour, dtype=int)

                if len(contour) > 2:
                    contours.append(contour)

    return contours


def scale_contours(contours: List[np.array], sf: float) -> List[np.array]:
    """Scale contours.
    
    Args:
        contours: List of (x, y) contours.
        sf: Scale factor.
        
    Returns:
        Contours after scaling.
        
    """
    for i, contour in enumerate(contours):
        contours[i] = (contour * sf).astype(contour.dtype)

    return contours
