"""Utility functions."""
from typing import List
from shapely.geometry.polygon import Polygon
import numpy as np
from geopandas import GeoSeries

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


def im_to_txt_path(impath: str, txt_dir: str = '/labels/', ext='txt'):
    """Replace the last occurance of /images/ to /labels/ in the given image 
    path and change extension to .txt
    
    Args:
        impath: Filepath to image.
        txt_dir: Replace last occurence of '/images/' with this value.
        ext: Replace with this extension.
    
    Returns:
        Updated filepath.
    
    """
    splits = impath.rsplit('/images/', 1)
    return splitext(f'/{txt_dir}/'.join(splits))[0] + f'.{ext}'


def corners_to_polygon(x1: int, y1: int, x2: int, y2: int) -> Polygon:
    """Return a Polygon from shapely with the box coordinates given the top left and bottom right corners of a 
    rectangle (can be rotated).
    
    Args:
        x1, y1, x2, y2: Coordinates of the top left corner (point 1) and the bottom right corner (point 2) of a box.
        
    Returns:
        Shapely polygon object of the box.
        
    """
    return Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])


def non_max_suppression(df, thr):
    """Apply non-max suppression (nms) on a set of prediction boxes. 
    Source: https://github.com/rbgirshick/fast-rcnn/blob/master/lib/utils/nms.py
    
    INPUTS
    ------
    df : dataframe
        data for each box, must contain the x1, y1, x2, y2, conf columns with point 1 being top left of the box and point 2 and bottom
        right of box
    thr : float
        IoU threshold used for nms
    
    RETURN
    ------
    df : dataframe
        remaining boxes
    
    """
    df = df.reset_index(drop=True)  # indices must be reset
    dets = df[['x1', 'y1', 'x2', 'y2', 'conf']].to_numpy()
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    scores = dets[:, 4]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr <= thr)[0]
        order = order[inds + 1]
        
    return df.loc[keep]


def remove_contained_boxes(df, thr):
    """Remove boxes contained in other boxes, or mostly contained. 
    
    INPUTS
    ------
    df : geodataframe
        info about each box
    thr : float
        the threshold of the box that must be contained by fraction of area to be remove
       
    RETURNS
    -------
    df : geodataframe
        the boxes that are left
    
    """
    rm_idx = []
    
    gseries = GeoSeries(df.geometry.tolist(), index=df.index.tolist())  # convert to a geoseries
    
    for i, geo in gseries.items():
        # don't check boxes that have already been removed
        if i not in rm_idx:
            r = df.loc[i]
            
            # remove boxes that don't overlap
            overlapping = df[
                (~df.index.isin(rm_idx + [i])) & ~((r.y2 < df.y1) | (r.y1 > df.y2) | (r.x2 < df.x1) | (r.x1 > df.x2))
            ]
            
            perc_overlap = overlapping.intersection(geo).area / overlapping.area  # percent of object inside the current geo
            
            # filter by the threshold
            overlapping = overlapping[perc_overlap > thr]
            
            rm_idx.extend(overlapping.index.tolist())
            
    return df.drop(index=rm_idx)
