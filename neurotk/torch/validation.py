# Functions used to validate trained models on a dataset of images.
import pandas as pd
from tqdm import tqdm
import numpy as np
from os.path import join

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .. import imwrite
from ..utils import create_dirs, get_filename
from ..torch.datasets import BinarySSDataset
from ..torchvision.semantic_segmentation_transforms import (
    Compose, ToTensor, Normalize, Resize
)

# source: https://hasty.ai/docs/mp-wiki/metrics/iou-intersection-over-union

def validate_semantic_segmentation(
    model: nn.Module, data: pd.DataFrame, save_dir: str = '.',
    img_size: int = 512, input_mode: str = 'rgb', batch_size: int = 6,
    device: str = 'cpu', thr: float = 0.7, smooth: float = 1e-6, 
    sigmoid: bool = False, save_figs: bool = False
) -> float:
    """Validate a semantic segmentation model on a dataset of images.
    
    Args:
        model (torch.nn.Module): Model.
        data (pandas.DataFrame): Image (fp column) and ground truth mask (label
            column) filepaths.
        save_dir (str): Directory to save files to.
        img_size (int): Size of images.
        input_mode (str): If 'rgb' then color normalization will be applied as 
            a transform.
        batch_size (int): For predicting in batches.
        device (str): Device to use when predicting, either 'cpu', 'cuda', or
            the id of the cuda device ('0', '1', etc.).
        thr (float): Threshold predictings by this value before calculating the
            metric.
        smooth: (float): Added when calculating IoU to avoid division by zero.
        sigmoid (bool): Apply sigmoid to the model output.
        save_figs (bool): Save prediction and a visualization mask for each 
            image.
        
    Returns:
        (float) Intersection over Union (IoU) value.
    
    """
    assert input_mode in ('grayscale', 'rgb')

    if device in ('cpu', 'cuda'):
        device = torch.device(device)
    else:
        device = torch.device(f'cuda:{device}')

    model.eval()
    model.to(device)
    
    if input_mode == 'rgb':
        transforms = Compose([
            ToTensor(), 
            Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            Resize((img_size, img_size)), 
        ])
    else:
        transforms = Compose([ToTensor(), Resize((img_size, img_size))])
                
    # Create dataloader.
    dataloader = DataLoader(
        BinarySSDataset(data, transforms=transforms), batch_size=batch_size, 
        shuffle=False
    )

    # Create subdirectories to same images.
    if save_figs:
        pred_dir = join(save_dir, 'predictions')
        vis_dir = join(save_dir, 'vis')
        
        create_dirs([pred_dir, vis_dir])
    
    # Track the intersection & union between ground truth and thresholded 
    # predictions.
    intersection = 0
    union = 0

    for batch in tqdm(dataloader):
        image, true = batch['image'], batch['mask']
        image = image.to(device)
        info = batch['info']

        with torch.no_grad():
            # Predict on batch.
            pred = model(image)
            
            if 'out' in pred:
                pred = pred['out']  # torchvision DeepLabV3 model.
                
            if sigmoid:
                # Apply Sigmoid to transform predictions between 0 and 1.
                pred = torch.sigmoid(pred)
            
            pred = pred.cpu().detach().numpy()

        # Threshold the prediction.
        pred = (pred > thr).astype(np.uint8) * 255
        true = true.numpy().astype(np.uint8) * 255
        
        if save_figs:
            # Save all the figures.
            for i in range(pred.shape[0]):
                # Save the predictions.
                p = pred[i][0]
                m = true[i][0]
                
                fn = get_filename(info['fp'][i], prune_ext=False)
                
                imwrite(join(pred_dir, fn), p)
                
                # Create a canvas of prediction overlays
                viz = np.zeros((img_size, img_size, 3), dtype=np.uint8)
                viz[np.where(p & m)] = (0, 255, 0)
                viz[np.where((p) & (~m))] = (255, 0, 0)
                viz[np.where((~p) & (m))] = (0, 0, 255)
                
                imwrite(join(vis_dir, fn), viz)
        
        # Add to the intersection and union.
        pred = pred.ravel()
        true = true.ravel()
        
        intersection += np.count_nonzero(pred & true)
        union += np.count_nonzero(pred | true)
        
    iou = (intersection + smooth) / (union + smooth)
    
    # Save the results.
    lines = f'Number of images: {len(data)}.\n'
    lines += f'Intersection over union (IoU): {iou:.6f}.\n'
    lines += f'Threshold value used: {thr}.'
    
    with open(join(save_dir, 'validation.txt'), 'w') as fh:
        fh.write(lines)
    
    return iou
