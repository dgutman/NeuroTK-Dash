import numpy as np


class EarlyStopping(object):
    """An early stopping class.

    To add in the future is using early stopping with a delta, currently
    the value must be smaller or value by any amount.

    Args:
        patience: Number of epochs before early stopping.
        direction: Direction that value should be changing for improvement,
            min: decreasing, max: increasing.
        verbose: If True it will print out a statement each iteration.

    Attibutes:
        patience: Number of epochs before early stopping.
        counter: Number of epochs without change.
        verbose: True to print out statements.
        value: Latest best value.
        direction: Direction value should change for improvement.

    Raises:
        ValueError if direction is not min or max.
    
    """
    def __init__(self, patience: int = 10, direction: str = 'min', 
                 verbose: bool = True):
        self.patience = patience
        self.counter = 0
        self.verbose = verbose

        if direction not in ('min', 'max'):
            raise ValueError('Direction parameter should be min or max.')

        if direction == 'min':
            self.value = np.inf
        else:
            self.value = -np.inf

        self.direction = direction

    def __call__(self, value: float) -> bool:
        """
        Args:
            value: Value to evaluate for performance, i.e. loss or metric.

        Returns:
            True if the number of epochs without improvement equals or is
            the same patience, otherwise False.
        
        """
        if self.direction == 'min' and value < self.value:
            self.counter = 0
            self.value = value

            if self.verbose:
                print(f'Early stopping value change ({value:.4f})')
        elif self.direction == 'max' and value > self.value:
            self.counter = 0
            self.value = value

            if self.verbose:
                print(f'Early stopping value change ({value:.4f})')
        else:
            self.counter += 1

            if self.counter >= self.patience:
                if self.verbose:
                    print('Early stopping.')
                return True
            else:
                if self.verbose:
                    print('No change in early stopping value for ' 
                          f'{self.counter} epochs.')
                return False
