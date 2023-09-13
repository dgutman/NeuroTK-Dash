from PIL import Image
from ..torchvision.semantic_segmentation_transforms import (
    Compose, ToTensor, Resize, Normalize
)
import torch
import cv2 as cv
import numpy as np


def predict_mask(model, img, size=256, norm=None, thresh=0.7):
    """Predict mask on the image given the model, and output the mask
    in the same aspect ratio as the input image.

    """
    model.eval()  # should not be modifying weights
    
    if isinstance(img, str):
        img = Image.open(img)
    elif isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    elif not isinstance(img, Image.Image):
        raise TypeError(
            'img must be a filepath string, ndarray, or PIL image'
        )

    if norm is None:
        # Default normalization values for ImageNet.
        norm = {
            'mean': [0.485, 0.456, 0.406],
            'std': [0.229, 0.224, 0.225]
        }

    # Get the original shape of the image.
    orig_shape = img.size

    # Apply transforms to image.
    transforms = Compose([
        ToTensor(),
        Resize((size, size)),
        Normalize(mean=norm['mean'], std=norm['std'])
    ])

    img = transforms(img, Image.new('L', orig_shape))[0]

    # Predict the mask.
    with torch.set_grad_enabled(False):
        pred = model(img.unsqueeze(0))['out'][0][0]

        # Treshold the mask to keep pixels which represent positives.
        mask = (pred.cpu().numpy() > thresh).astype(np.uint8) * 255

        # Reformat the mask to its original size.
        mask = cv.resize(mask, orig_shape, None, None, cv.INTER_NEAREST)

        return mask
