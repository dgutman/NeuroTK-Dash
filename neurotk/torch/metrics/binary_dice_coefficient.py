# Still a work in progress.
import numpy as np


class binary_dice_coefficient():
    """Initialize a dice coefficient metric when dealing with two classes:
    positive and background class.
    
    """
    def __init__(self):
        """Initialize the metric."""
        self.intersection = 0  # intersection
        self.total = 0  # total pixels in both images

    def update(self, logits, targets):
        """Update the fields."""
        # Convert logits to predictions.
        preds = (logits.data.cpu().numpy().ravel() > 0.1)
        true = (targets.data.cpu().numpy().ravel() > 0)

        self.intersection += np.count_nonzero(preds * true)
        self.total += np.count_nonzero(preds) + np.count_nonzero(true)

    def compute(self):
        """Compute the Dice coefficient."""
        return 2 * self.intersection / self.total
        
    def reset(self):
        """Reset the fields."""
        self.intersection = 0
        self.total = 0
