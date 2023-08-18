from torchvision import models
from torchvision.models.segmentation.deeplabv3 import (
    DeepLabHead, DeepLabV3_ResNet101_Weights
)


def deeplabv3_model(classes: int = 1):
    """DeepLabV3 model with custom number of output classes / channels.
    
    Args:
        classes: The number of output channels or classes.

    Returns:
        Model in default train status.
        
    """
    model = models.segmentation.deeplabv3_resnet101(
        weights=DeepLabV3_ResNet101_Weights.COCO_WITH_VOC_LABELS_V1,
        progress=False,
    )
    
    model.classifier = DeepLabHead(2048, classes)
    model.train()
    
    return model
