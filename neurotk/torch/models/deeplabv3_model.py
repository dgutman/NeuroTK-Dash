from torchvision import models
import torch.nn as nn
from torchvision.models.segmentation.deeplabv3 import (
    DeepLabHead, DeepLabV3_ResNet101_Weights
)


def deeplabv3_model(classes: int = 1, input_mode: str = 'rgb'):
    """DeepLabV3 model with custom number of output classes / channels.
    
    Args:
        classes: The number of output channels or classes.
        input_mode: Either 'rgb' or 'grayscale' for the type of images you 
            are using.

    Returns:
        Model in default train status.
        
    """
    model = models.segmentation.deeplabv3_resnet101(
        weights=DeepLabV3_ResNet101_Weights.COCO_WITH_VOC_LABELS_V1,
        progress=False,
    )

    if input_mode == 'grayscale':
        # Source: https://discuss.pytorch.org/t/how-to-modify-deeplabv3-and-fcn-models-for-grayscale-images/52688
        # Change to have a single input channel.
        model.backbone.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, 
                                         padding=3, bias=False)   
    elif input_mode != 'rgb':
        raise Exception('input_mode has to be grayscale or rgb')
    
    model.classifier = DeepLabHead(2048, classes)
    model.train()
    
    return model
