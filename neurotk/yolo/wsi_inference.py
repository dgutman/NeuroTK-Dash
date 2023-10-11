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
    contained_thr: float = 0.8, mask_thr: float = (0.2)
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
        mask_thr (float): Fraction of tile that must be in mask to be predicted
            on.
            
    """
    # Get image tilesource, currently throwing warnings for these images.
    ts = large_image.getTileSource(fp)
    
    ts_metadata = ts.getMetadata()
    fr_h = ts_metadata['sizeY']
        
    if mag is not None and ts_metadata['magnification'] is not None:
        # Mult. factor: Desired magnification -> Scan magnifiction
        mag_to_fr = ts_metadata['magnification'] / mag
        
        fr_tile_size = int(tile_size * mag_to_fr)
        fr_stride = int(stride * mag_to_fr)
    else:
        mag_to_fr = 1
        fr_tile_size, fr_stride = tile_size, stride
        
    # Calculate some scale factors.
    if mask is not None:
        # Definitions are when using the scale factor as a multiplicative factor.
        # Full resolution -> mask resolution.
        fr_to_mask = mask.shape[0] / fr_h
        
        mask_tile_size = int(fr_tile_size * fr_to_mask)
        mask_tile_area = mask_tile_size ** 2
    
    # Calculate the x, y coordinates of the top left of each tile.
    xys = []
            
    for y in range(0, ts_metadata['sizeY'], fr_stride):
        for x in range(0, ts_metadata['sizeX'], fr_stride):
            if mask is None:
                xys.append((x, y, None, None, None))
            else:
                # Get the low res mask tile.
                x1, y1 = int(x * fr_to_mask), int(y * fr_to_mask)
                                
                mask_tile = mask[
                    y1:y1+mask_tile_size, x1:x1+mask_tile_size
                ]
                                
                pos_frac = np.count_nonzero(mask_tile) / mask_tile_area
                
                if pos_frac > mask_thr:
                    xys.append((x, y, x1, y1, pos_frac))
                        
    pred_df = []  # track all predictions in dataframe
    
    # Predict on tiles in batches.
    idx = list(range(0, len(xys), batch_size))
    
    print(f'Predicting on tiles for {len(idx)} batches.')
    for i in tqdm(idx):
        imgs = []
        
        batch_xys = xys[i:i+batch_size]
        
        for xy in batch_xys:
            x, y, tile_x, tile_y, tile_frac = xy
            
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
            else:
                # Convert image to BGR.
                img = cv.cvtColor(img[:, :, :3], cv.COLOR_RGB2BGR)
                                                
            # Pad the image if needed
            if img_shape[:2] != (tile_size, tile_size):
                img = cv.copyMakeBorder(
                    img, 0, tile_size - img_shape[0], 0, 
                    tile_size - img_shape[1], cv.BORDER_CONSTANT, None, fill
                )
                
            if mask is not None:
                if tile_frac < 1:
                    # Mask out region.
                    mask_tile = mask[
                        tile_y:tile_y+mask_tile_size,
                        tile_x:tile_x+mask_tile_size
                    ].copy()
                
                    # Reshape mask to tile image size.
                    mask_tile = cv.resize(
                        mask_tile.copy(), (tile_size, tile_size), 
                        interpolation=cv.INTER_NEAREST
                    )
                    
                    # Regions outside of mask get set to fill value.
                    img = img.copy()
                    
                    img[mask_tile == 0] = fill
                
            imgs.append(img)
            
        batch_out = model.predict(
            imgs,
            device=device,
            max_det=max_det,
            iou=iou_thr,
            conf=conf_thr,
            imgsz=tile_size,
            verbose=False,
            stream=True
        )
        
        for xy, out in zip(batch_xys, batch_out):
            x, y = xy[:2]
            
            boxes = out.boxes
                        
            for label, box, cf in zip(boxes.cls, boxes.xyxy, boxes.conf):
                box = box.cpu().detach().numpy()
                label = label.cpu().detach().numpy()
                cf = cf.cpu().detach().numpy()
                
                # Keep the magnification in mind.
                x1 = int(box[0] * mag_to_fr) + x
                y1 = int(box[1] * mag_to_fr) + y
                x2 = int(box[2] * mag_to_fr) + x
                y2 = int(box[3] * mag_to_fr) + y
                        
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
    
    if len(pred_df):
        pred_df = non_max_suppression(pred_df, iou_thr)
        pred_df = remove_contained_boxes(pred_df, contained_thr)
        
    print(f'    {len(pred_df)} numbers of predictions returned.')
    
    return pred_df
    