from typing import Optional
import torch
import numpy as np
from tqdm import tqdm
from . import EarlyStopping
from tqdm import tqdm

from os import makedirs
from os.path import join
                

def train_binary_ss_model(
    model, 
    dataloaders: dict,
    criterion,  
    optimizer, 
    metrics: Optional[dict] = None, 
    epochs: int = 10,
    device: Optional[str] = None,
    early_stopper: Optional[EarlyStopping] = None,
    save_dir: Optional[str] = None
):
    """Train a semantic segmentation model were the masks / labels only
    contains 0 and 1 values (background and positive class).
    
    Args:
        model: Model that will predict probability masks, i.e. pixel wise
            predictions.
        dataloaders: Contains dataloaders at the 'train' and 'val' keys.
        criterion: PyTorch criterion to calculate loss.
        optimizer: Determine backpropagation strategy.
        metrics: Metrics that have the update, reset, and compute methods.
        epochs: Number of epochs to train to.
        device: Specify device to use, otherwise it will use the first 
            cuda device available otherwise cpu.
        early_stopper: Object to pass loss value on validation every epoch,
            will early stop the training early if criteria met.
        save_dir: Location to save best and last weights.

    Returns:
        Trained model.
        
    """
    if save_dir is not None:
        makedirs(save_dir, exist_ok=True)
    
    # Create empty metrics if not given.
    if metrics is None:
        metrics = {}

    if device is None:
        # By default use the first GPU if available.
        device = torch.device(
            "cuda:0" if torch.cuda.is_available() else "cpu"
        )
    
    model.to(device)

    # Get size of train and validation datasets.
    sizes = {phase: len(dataloaders[phase].dataset) for phase in ['train', 
                                                                  'val']}

    best_loss = np.inf
    
    for epoch in range(1, epochs + 1):
        epoch_str = f'Epoch {epoch} of {epochs}'
        print(epoch_str)
        print('-' * len(epoch_str))

        for phase in ['train', 'val']:
            # Set model to appropriate state.
            model.train() if phase == 'train' else model.eval()

            # reset metrics
            for metric in metrics.values():
                metric.reset()

            # Iterate through batches.
            epoch_loss = 0
            
            for sample in tqdm(dataloaders[phase]):
                # Send input and label masks to same device as model.
                inputs = sample['image'].to(device)
                targets = sample['mask'].to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    # Predict the masks.
                    outputs = model(inputs)

                    # Calculate the loss.
                    loss = criterion(outputs['out'], targets)

                    # Backpropagation and step the optimizer.
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                    # Update metrics.
                    for metric in metrics.values():
                        metric.update(
                            outputs['out'], 
                            targets
                        )

                    loss = loss.detach().item()
                    epoch_loss += loss

            # Normalize the loss sum of mini-batches by the number of images
            epoch_loss = epoch_loss / sizes[phase]

            # Save model as best if epoch loss improve

            # Report epoch loss and metrics.
            # JC: still hard coded in the metric.
            report_str = f'({phase}) loss: {epoch_loss:.4f}'

            for metric_name, metric_val in metrics.items():
                report_str += f', {metric_name}: {metric_val.compute():.4f}'

            print(report_str)         

            if phase == 'val':
                if epoch_loss < best_loss:
                    best_loss = epoch_loss

                    if save_dir is not None:
                        torch.save(model.state_dict(), 
                                   join(save_dir, 'best.pt'))
                
                if early_stopper is not None and early_stopper(epoch_loss):
                    if save_dir is not None:
                        torch.save(model.state_dict(),
                                   join(save_dir, 'last.pt'))
                    return model
        print()

    # Save last model.
    if save_dir is not None:
        torch.save(model.state_dict(), join(save_dir, 'last.pt'))

    return model
