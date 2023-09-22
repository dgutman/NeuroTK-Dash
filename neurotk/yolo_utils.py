from typing import Union, Tuple
import numpy as np


def convert_box_type(box: np.ndarray) -> np.ndarray:
    """Convert a box type from YOLO format (x-center, y-center, box-width,
    box-height) to (x1, y1, x2, y2) where point 1 is the top left corner of box 
    and point 2 is the bottom right corner.
    
    Args:
        box (np.ndarray): [N, 4], each row a point and the format being 
            (x-center, y-center, box-width, box-height).
        
    Returns:
        new_box (np.ndarray): [N, 4] each row a point and the format x1, y1, x2,
        y2.
        
    """
    # get half the box height and width
    half_bw = box[:, 2] / 2
    half_bh = box[:, 3] / 2
    
    new_box = np.zeros(box.shape, dtype=box.dtype)
    new_box[:, 0] = box[:, 0] - half_bw
    new_box[:, 1] = box[:, 1] - half_bh
    new_box[:, 2] = box[:, 0] + half_bw
    new_box[:, 3] = box[:, 1] + half_bh
    
    return new_box


def read_yolo_label(
    fp: str, img_shape: Union[int, Tuple[int, int], None] = None, 
    shift: Union[int, Tuple[int, int], None] = None, 
    convert: bool = False
) -> np.ndarray:
    """Read a yolo label text file. It may contain a confidence value for the 
    labels or not, will handle both cases
    
    Args:
        fp (str): The path of the text file.
        img_shape (Union[int, Tuple[int, int], None]): Image width and 
            height corresponding to the label, if an int it is assumed both 
            are the same. Will scale coordinates to int values instead of 
            normalized if given.
        shift (Union[int, Tuple[int, int], None]): Shift value in the x and 
            y direction, if int it is assumed to be the same in both. These 
            values will be subtracted and applied after scaling if needed. 
        convert (bool): If True, convert the output boxes from yolo format 
            (label, x-center, y-center, width, height, conf) to (label, x1, y1, 
            x2, y2, conf) where point 1 is the top left corner of box and point 
            2 is the bottom corner of box.
    
    Returns:
        (np.ndarray) Coordinates array, [N, 4 or 5] depending if confidence was
        in input file.
    
    """
    coords = []
    
    with open(fp, 'r') as fh:
        for line in fh.readlines():
            if len(line):
                coords.append([float(ln) for ln in line.strip().split(' ')])
                
    coords = np.array(coords)
    
    # scale coords if needed
    if img_shape is not None:
        if isinstance(img_shape, int):
            w, h = img_shape, img_shape
        else:
            w, h = img_shape[:2]
            
        coords[:, 1] *= w
        coords[:, 3] *= w
        coords[:, 2] *= h
        coords[:, 4] *= h
        
    # shift coords
    if shift is not None:
        if isinstance(shift, int):
            x_shift, y_shift = shift, shift
        else:
            x_shift, y_shift = shift[:2]
            
        coords[:, 1] -= x_shift
        coords[:, 2] -= y_shift
        
    if convert:
        coords[:, 1:5] = convert_box_type(coords[:, 1:5])
        
    return coords
