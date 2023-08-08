from pandas import DataFrame
from torch.utils.data import Dataset
from typing import Optional, Callable
from PIL import Image


class BinarySSDataset(Dataset):
    """A PyTorch dataset for image segmentation for binary tasks.

    """
    def __init__(
        self, 
        data: DataFrame,
        transforms: Optional[Callable] = None,
        image_color_mode: str = 'rgb',
        norm: Optional[Callable] = None
    ) -> None:
        """
        Args:
            data: Dataframe with "fp" and "label" columns which are the 
                filepaths to the image and mask label.
            transforms: Image transforms to apply to the image and mask.
            image_color_mode: mode of image, 'rgb' or 'grayscale'
            norm: A normalization transform to apply to the images after
                all the other transforms.
        
        Raises:
            ValueError: If image_color_mode is not 'rgb' or 'grayscale'.
            ValueError: If data does not contain 'fp' or 'label' columns.
            
        """
        if 'fp' not in data:
            raise ValueError('fp column not in data')
        if 'label' not in data:
            raise ValueError('label column not in data')

        if image_color_mode not in ('rgb', 'grayscale'):
            raise ValueError(
                f'{image_color_mode} is an invalid choice. '
                'Please enter from rgb grayscale.'
            )
                     
        self.data = data
        self.transforms = transforms
        self.image_color_mode = image_color_mode
        self.norm = norm

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> dict:
        """Get image, mask, and additional data.
        
        Args:
            index: Image index.
            
        Returns:
            Image and mask as tensors and dictionary of additional data from
            input Datframe.
            
        """
        # Get paths.
        image_path = self.data.iloc[index].fp
        mask_path = self.data.iloc[index].label

        # Open files with automatic closing when done.
        with open(image_path, "rb") as image_file, open(mask_path,
                                                        "rb") as mask_file:
            # Image is read as RGB and mask as grayscale for binary problem.
            image = Image.open(image_file)
                                                            
            if self.image_color_mode == "rgb":
                image = image.convert("RGB")
            else:
                image = image.convert("L")
            
            mask = Image.open(mask_file).convert('L')

            # Apply transforms
            sample = {"image": image, "mask": mask,
                      'info': self.data.iloc[index].to_dict()}
                                                            
            if self.transforms:
                sample["image"] = self.transforms(sample["image"])
                sample["mask"] = self.transforms(sample["mask"])

            if self.norm:
                # Color normalize the image.
                sample['image'] = self.norm(sample['image'])
            
            return sample
