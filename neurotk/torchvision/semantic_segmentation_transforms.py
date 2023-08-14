from PIL import Image
from typing import Union, List, Tuple, Optional
import random
from torch import Tensor

import torchvision.transforms as transforms
import torchvision.transforms.functional as F
from torchvision.transforms import InterpolationMode


class Compose(object):
    """Apply a list of semantic segmentation transforms to an image and label
    mask.

    Args:
        transforms: Transforms to apply to image and mask in order.

    Attributes:
        transforms (list): List of transforms.
    
    """
    def __init__(self, transforms: list):
        self.transforms = transforms
        
    def __call__(self, image: Image, mask: Image):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask after transformations.
        
        """
        for transform in self.transforms:
            image, mask = transform(image, mask)
            
        return image, mask


class ToTensor(object):
    """Transform image and mask to tensor.     
    
    """
    def __call__(self, image: Union[Image, Tensor], 
                 mask: Union[Image, Tensor]):
        """    
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.
        
        """
        # convert image to tensor
        transform = transforms.ToTensor()
        image = transform(image)
        mask = transform(mask)
        
        return image, mask


class Normalize(object):
    """Color normalize an image, label mask is passed but not normalized.
    
    Args:
        mean: RGB mean.
        std: RGB standard deviation.
        
    Attributes:
        transform (torchvision.transforms.Normalize): Normailze transform.
        
    """
    def __init__(self, mean: [int, int, int], std: [int, int, int]):
        self.transform = transforms.Normalize(mean=mean, std=std)
        
    def __call__(self, image: Union[Image, Tensor], 
                 mask: Union[Image, Tensor]):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.
        
        """
        return self.transform(image), mask


class Resize(object):
    """Resize input image or tensor and its label mask. Label mask is always
    resized with nearest exact interpolation to keep only unique labels.
    
    Args:
        size: Size to resize input to.
        interpolation: Interpolation method for image, see docstring for 
            torchvision.transforms.Resize for details.
        antialias: Apply antialias to the image, see docstring for 
            torchvision.transforms.Resize for details.

    Attributes:
        transform (torchvision.transforms.Resize): Transform applied to image.
        label_transform (torchvision.transforms.Resize): Transform applied to
            label masks.
            
    """
    def __init__(
        self, 
        size: int | List[int], 
        interpolation: InterpolationMode = InterpolationMode.BILINEAR, 
        antialias: bool = True
    ):
        self.transform = transforms.Resize(size, interpolation=interpolation,
                                           antialias=antialias)
        self.label_transform = transforms.Resize(
            size, interpolation=InterpolationMode.NEAREST_EXACT
        )

    def __call__(self, image: Union[Image, Tensor], 
                 mask: Union[Image, Tensor]):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.

        """
        return self.transform(image), self.label_transform(mask)


class RandomHorizontalFlip(object):
    """Randomly flip an image horizontally.
    
    Args:
        Probability that the image will flip.

    Attributes:
        p: Probability of image flipping.
    
    """
    def __init__(self, p: float = 0.5):
        self.p = p
        
    def __call__(self, image: Union[Image, Tensor], 
                 mask: Union[Image, Tensor]):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.

        """
        if random.random() < self.p:
            image = F.hflip(image)
            mask = F.hflip(mask)
        
        return image, mask
    
    
class RandomVerticalFlip():
    """Randomly flip an image vertically.
    
    Args:
        Probability that the image will flip.

    Attributes:
        p: Probability of image flipping.
    
    """
    def __init__(self, p=0.5):
        self.p = p
        
    def __call__(self, image: Union[Image, Tensor], 
                 mask: Union[Image, Tensor]):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.

        """
        if random.random() < self.p:
            image = F.vflip(image)
            mask = F.vflip(mask)
        return image, mask
    
    
class RandomRotation():
    """Random rotation of an image.
    
    Args:
        degrees: Degrees to rotate image by. If a single value it will be 
            rotated from negative to positive of this degree otherwise it 
            should be two values: the min and max degree of rotation.
        border_values: Value to use to fill in image after rotation. If a
            single value it will be used in all channels.
        ignore_index: For mask this value will be used to fill in areas
            after rotation.
        expand: If True will expand the image to fit the entire rotated 
            image. Note that this may result in your output image being
            different size than the input image.
        center: Point to rotate around, default None option is the center
            of image.
        interpolation: Interpolation mode for image from 
            interpoloation.transforms.InterpolationMode. Mask is always
            interpolated with NEAREST option.

    Attributes:
        expand: Expand to include image after rotation.
        center: Center point to expand on, None default to center.
        fill: Value to fill image when rotated.
        ignore_index: Value to fill mask when rotated.
        interpolation: Interpolation method for image.
        degrees: Min and max value to rotate image and mask.
        
    Raises:
        ValueError if degrees is not a single int or a tuple or size 2.
    
    """
    def __init__(
        self, degrees: Union[int, Tuple[int, int]], #int | List[int], 
        fill: Union[int, Tuple[int, int]] = 255, ignore_index: int = 0, 
        expand: bool = False, center: Optional[bool] = None, 
        interpolation: InterpolationMode = InterpolationMode.NEAREST
    ):
        self.expand = expand
        self.center = center
        self.fill = fill
        self.ignore_index = ignore_index
        self.interpolation = interpolation
        
        if isinstance(degrees, int):
            self.degrees = list(range(-abs(degrees), abs(degrees)+1))
        elif len(degrees) == 2:
            self.degrees = degrees
        else:
            raise ValueError('degrees must be single int or a sequence (min, max)')
            
    def __call__(self, image, mask):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.

        """
        # Calculate the random degrees to rotate by.
        degree = random.sample(self.degrees, 1)[0]
        
        # add a dummy dimension
        # *Note: RandomRotation function works on tensors but it must have a shape of ...xHxW where ... is an arbitrary leading dimensions, these must be present
        #        so we artifically add 1
        mask = mask.unsqueeze(0)

        im_rotator = transforms.RandomRotation(
            [degree, degree], expand=self.expand, center=self.center, 
            fill=self.fill, interpolation=self.interpolation
        )
        mask_rotator = transforms.RandomRotation(
            [degree, degree], expand=self.expand, center=self.center, 
            fill=self.ignore_index, interpolation=InterpolationMode.NEAREST
        )
        
        return im_rotator(image), mask_rotator(mask).squeeze(0)


class ColorJitter():
    """Apply random color jitter to an image.

    For original description of parameters see:
    torchvision.transforms.ColorJitter. All jitters are randomly chosen 
    from a uniformally distributed values from min and max provided by each
    parameter. If a single value is given then the min and max is 
    calculated as [max(0, 1 - parameter), 1 + parameter].
    
    Args:
        brightness: Jitter brightness.
        contrast: Jitter contrast.
        saturation: Jitter saturation.
        hue: Jitter hue.

    Attributes:
        colorjitter: Torchvision transform to color jitter image.
    
    """
    def __init__(self, brightness=0, contrast=0, saturation=0, hue=0):
        self.colorjitter = transforms.ColorJitter(
            brightness=brightness, contrast=contrast, 
            saturation=saturation, hue=hue
        )
        
    def __call__(self, image: Union[Image, Tensor], 
                 mask: Union[Image, Tensor]):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.

        """  
        return self.colorjitter(image), mask
