# Train a DeepLabV3 (semantic segmentation) model to detect tissue in low
# resolution WSIs.
import sys
sys.path.append('../..')

from argparse import ArgumentParser
from pandas import read_csv
from sklearn.model_selection import train_test_split

import torch
from torch.utils.data import DataLoader

from neurotk.torch import EarlyStopping, train_binary_ss_model
from neurotk.torch.datasets import BinarySSDataset
from neurotk.torch.models import deeplabv3_model
from neurotk.torch.metrics import binary_dice_coefficient
from neurotk.torchvision.semantic_segmentation_transforms import (
    Normalize, ToTensor, Resize, RandomHorizontalFlip, RandomVerticalFlip,
    RandomRotation, ColorJitter, Compose
)


def parse_opt():
    """Read the CLIs."""
    parser = ArgumentParser()
    
    parser.add_argument('--save-dir', type=str, 
                        help='Directory to save model weights to.')
    parser.add_argument(
        '--dataset-fp', type=str, 
        default='/jcDataStore/Data/NeuroTK-Dash/ml-tissue-detection/tissue-dataset.csv',
        help='Filepath to CSV file with filepaths to images and masks.'
    )
    parser.add_argument('--val-frac', type=float, default=0.2, 
                        help='Fraction of images to use as validation')
    parser.add_argument('--random-state', type=float, default=64,
                        help='Seed random state of splitting data')
    parser.add_argument('--size', type=int, default=256, 
                        help='Size of image to train on.')
    parser.add_argument('--batch-size', type=int, default=8,
                        help='Batch size.')
    parser.add_argument('--epochs', type=int, default=100, 
                        help='Number of epochs to train for.')
    parser.add_argument(
        '--patience', type=int, default=20,
        help='Number of epochs without improvement before early stopping.'
    )
    parser.add_argument('--lr', type=float, default=1e-4, 
                        help='Learning rate.')

    return parser.parse_args()
    

def main():
    """Main function."""
    opt = parse_opt()

    # Read the dataset dataframe.
    df = read_csv(opt.dataset_fp)

    # Split the dataframe into train and val.
    train_df, val_df = train_test_split(df, test_size=opt.val_frac, 
                                    random_state=opt.random_state)

    # Data augmentation transforms.
    norm = Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

    transforms = Compose([
        ToTensor(), 
        Resize((opt.size, opt.size)), 
        RandomHorizontalFlip(), 
        RandomVerticalFlip(), 
        RandomRotation(90, fill=1),
        ColorJitter(brightness=0.1, contrast=0.005, saturation=0.2, hue=0.02),
        norm
    ])
    
    val_transforms = Compose([
        ToTensor(),
        Resize((opt.size, opt.size)),
        norm
    ])
    
    # Create dataloaders, set as dictionary with 'train' and 'val'.
    dataloaders = {
        'train': DataLoader(
            BinarySSDataset(train_df, transforms=transforms), 
            batch_size=opt.batch_size, 
            shuffle=True
        ),
        'val': DataLoader(
            BinarySSDataset(val_df, transforms=val_transforms), 
            batch_size=opt.batch_size, 
            shuffle=False
        )
    }

    # Create model.
    model = deeplabv3_model()
    
    # Optimizer gets fed in the model parameters and learning rate.
    optimizer = torch.optim.Adam(model.parameters(), lr=opt.lr)
    
    # Specify the loss function
    criterion = torch.nn.MSELoss(reduction='mean')
    
    # Set up the metrics
    metrics = {'dice coefficient': binary_dice_coefficient()}

    # Train model.
    _ = train_binary_ss_model(
        model,
        dataloaders,
        criterion,
        optimizer,
        metrics,
        epochs=opt.epochs,
        device=None,
        early_stopper=EarlyStopping(patience=opt.patience),
        save_dir=opt.save_dir
    )


if __name__ == '__main__':
    main()