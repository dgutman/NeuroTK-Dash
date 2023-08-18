from torch import Tensor


class UnNormalize(object):
    """Reverse the color normalization transform on a tensor.

    Source: https://discuss.pytorch.org/t/simple-way-to-inverse-transform-normalization/4821
    
    Args:
        mean: RGB mean.
        std: RGB standard deviation.
        
    Attributes:
        mean: RGB mean.
        std: RGB standard deviation.
        
    """
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, tensor: Tensor) -> Tensor:
        """
        Args:
            tensor: Tensor image of size (C, H, W) to be reversed normalized.
            
        Returns:
            Normalized image.
        
        """
        for t, m, s in zip(tensor, self.mean, self.std):
            t.mul_(s).add_(m)

        return tensor
