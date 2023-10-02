from typing import Optional, Tuple
import torch.nn as nn
import numpy as np
import large_image
from tqdm import tqdm
import cv2 as cv
from shapely.geometry import Polygon
from geopandas import GeoDataFrame
from ..utils import non_max_suppression, remove_contained_boxes


def wsi_inference(
    fp: str, model: nn.Module, mask: Optional[np.ndarray] = None, 
    frame: Optional[int] = None, mag: Optional[float] = None,
    tile_size: int = 1280, stride: int = 960, batch_size: int = 10,
    device: str = 'cpu', max_det: int = 1000, iou_thr: float = 0.6, 
    conf_thr: float = 0.5, fill: Tuple[int, int, int] = (255, 255, 255),
    contained_thr: float = 0.8 
):
    """Inference a YOLO model on a large image by tiling it into smaller 
    overlapping regions and then merging predictions.
    
    Args:
        fp (str): Filepath to image, must be openable by large_image.
        model (torch.nn.Module): Model used to predict labels.
        mask (numpy.ndarray): Optional low resolution mask used to narrow
            down the regions to analyze in the image. If None then the entire
            image is analyzed.
        frame (int): Optional frame of multiplex image to analyze.
        mag (int): Optional magnification to analyze images at.
        tile_size (int): Tile size.
        stride (int): Stride size during tiling.
        batch_size (int): Number of images to predict in bulk.
        device (str): Options are 'cuda', 'cpu', or the ids of GPU devices (i.e.
            0,1,2,etc.).
        max_det (int): Maximum number of detection per tile.
        iou (float): IoU threshold when running NMS during prediction in a tile.
        conf (float): Confidence threshold, predictions below this threshold are
            discarded.
        fill (Tuple[int, int, int]): RGB color to fill tiles regions to not be
            analyzed.
        
            
    """
    # Get image tilesource, currently throwing warnings for these images.
    ts = large_image.getTileSource(fp)
    
    ts_metadata = ts.getMetadata()
        
    if mag is not None and ts_metadata['magnification'] is not None:
        # Mult. factor: Desired magnification -> Scan magnifiction
        fr_to_mag = ts_metadata['magnification'] / mag
        fr_tile_size = int(tile_size * fr_to_mag)
        fr_stride = int(stride * fr_to_mag)
    else:
        fr_tile_size, fr_stride = tile_size, stride
    
    # Calculate the x, y coordinates of the top left of each tile.
    xys = []
    
    for y in range(0, ts_metadata['sizeY'], fr_stride):
        for x in range(0, ts_metadata['sizeX'], fr_stride):
            if mask is None:
                xys.append((x, y))
            else:
                print("Mask support not currently available, defaulting to "
                      "include all tiles.")
                # Add logic here checking if this tile is sufficiently enough
                # to include for predicting.
    
    pred_df = []  # track all predictions in dataframe
    
    # Predict on tiles in batches.
    idx = list(range(0, len(xys), batch_size))
    
    print(f'Predicting on tiles for {len(idx)} batches.')
    for i in tqdm(idx):
        imgs = []
        
        batch_xys = xys[i:i+batch_size]
        
        for xy in batch_xys:
            x, y = xy
            
            img = ts.getRegion(
                region={
                    'left': x, 'top': y, 
                    'right':x + fr_tile_size, 'bottom': y + fr_tile_size
                },
                format=large_image.constants.TILE_FORMAT_NUMPY,
                scale={'magnification': mag},
                frame=frame
            )[0]
            
            img_shape = img.shape
                        
            if img_shape[2] == 1:
                img = cv.cvtColor(img[:, :, 0], cv.COLOR_GRAY2RGB)
                                                
            # Pad the image if needed
            if img_shape[:2] != (tile_size, tile_size):
                img = cv.copyMakeBorder(
                    img, 0, tile_size - img_shape[0], 0, 
                    tile_size - img_shape[1], cv.BORDER_CONSTANT, None, fill
                )     
                
            imgs.append(img)
            
        batch_out = model.predict(
            imgs,
            device=device,
            max_det=max_det,
            iou=iou_thr,
            conf=conf_thr,
            imgsz=tile_size,
            verbose=False
        )
        
        for xy, out in zip(batch_xys, batch_out):
            x, y = xy
            
            boxes = out.boxes
            
            for label, box, cf in zip(boxes.cls, boxes.xyxy, boxes.conf):
                box = box.cpu().detach().numpy()
                label = label.cpu().detach().numpy()
                cf = cf.cpu().detach().numpy()
                
                x1, y1, x2, y2 = box[0] + x, box[1] + y, box[2] + x, box[3] + y
                        
                pred_df.append([
                    int(label), x1, y1, x2, y2, cf,
                    Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]), 
                    (x2-x1)*(y2-y1)
                ])
           
    # Compile boxes into dataframe.     
    pred_df = GeoDataFrame(
        pred_df, 
        columns=['label', 'x1', 'y1', 'x2', 'y2', 'conf', 'geometry', 
                 'box_area']
    )
    
    print(f"Merging overlapping boxes from a starting {len(pred_df)} boxes...")
    pred_df = non_max_suppression(pred_df, iou_thr)
    pred_df = remove_contained_boxes(pred_df, contained_thr)
    print(f'    {len(pred_df)} final predicted boxes.')
    
    return pred_df