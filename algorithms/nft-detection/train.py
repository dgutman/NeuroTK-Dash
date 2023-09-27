# Train a new model.
from ultralytics import YOLO
from argparse import ArgumentParser
import yaml
import pickle
from os.path import join
from copy import deepcopy


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--data', type=str, help='Dataset YAML file.')
    parser.add_argument('--project', type=str, default='models',
                        help='Directory to put model subdirectories.')
    parser.add_argument('--name', type=str, default='exp',
                        help='Model directory.')
    parser.add_argument('--exist-ok', action='store_true',
                        help='Overwrite files.')
    parser.add_argument('--device', type=str, default=0,
                        help='GPU ids, such as 0, 1, 2 or [0, 1] or cpu.')
    parser.add_argument('--weights', type=str, default='yolov8m.pt',
                        help='Pretrained weights to start with.')
    parser.add_argument('--epochs', type=int, default=100, 
                        help='Number of epochs to train to.')
    parser.add_argument('--batch', type=int, default=8, help='Batch size.')
    parser.add_argument('--patience', type=int, default=20, 
                        help='Epochs without improvement before early stop.')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Size of images.')
    parser.add_argument(
        '--params', type=str, default='params.yaml',
        help='YAML file with key-word arguments to pass to train function.'
    )
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    # Read key-word arguments.
    with open(args.params, 'r') as fh:
        kwargs = yaml.safe_load(fh)

    # Train model.
    model = YOLO(args.weights)

    print(args)
    results = model.train(
        data=args.data,
        project=args.project,
        name=args.name,
        exist_ok=args.exist_ok,
        device=args.device,
        epochs=args.epochs,
        batch=args.batch,
        patience=args.patience,
        imgsz=args.imgsz,
        model=args.weights,
        **kwargs
    )

    # Save the results.
    with open(join(args.project, args.name, 'results.pkl'), 'wb') as fh:
        save_dict = {
            # Probably don't need deepcopy.
            'ap_class_index': deepcopy(results.ap_class_index),
            'keys': deepcopy(results.keys),
            'maps': deepcopy(results.maps),
            'fitness': deepcopy(results.fitness),
            'names': deepcopy(results.names),
            'results_dict': deepcopy(results.results_dict),
            'speed': deepcopy(results.speed)
        }
        pickle.dump(save_dict, fh)


if __name__ == '__main__':
    main()