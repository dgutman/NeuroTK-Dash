# Make neurotk Python module (from dgutman/NeuroTK-Dash repository) available.
import sys
sys.path.append('/opt/scw/NeuroTK-Dash')

from ultralytics import YOLO
from histomicstk.cli.utils import CLIArgumentParser  # for CLI implementation
# from argparse import ArgumentParser  # for developing outside CLI implementation
from neurotk.yolo import wsi_inference
import json


# def parse_args():
#     """Used for developing and testing script outside of CLI."""
#     parser = ArgumentParser()
    
#     parser.add_argument(
#         '--in-file', type=str,
#         default='/opt/scw/data/example-dapi-multiplex-image.lif'
#     )
#     parser.add_argument('--frame', type=int, default=2)
#     parser.add_argument('--device', type=str, default='cuda')
#     parser.add_argument('--max-det', type=int, default=1000)
#     parser.add_argument('--iou-thr', type=float, default=0.4)
#     parser.add_argument('--conf-thr', type=float, default=0.5)
#     parser.add_argument('--contained-thr', type=float, default=0.6)
#     parser.add_argument('--docname', type=str, default='cli-test')
    
#     return parser.parse_args()


def main(args):
    """Detect nuclei with pre-trained YOLO model and inference results back
    to the DSA as annotations.
    
    """
    import torch
    
    print('Is cuda available?')
    print(torch.cuda.is_available())
    
    # Load model.
    print('Trying to load YOLO weights')
    model = YOLO('/opt/scw/cli/DAPINucleiDetection/best.pt')
    print("YOLO weights loaded.")
    
    print('Inferencing....')
    pred_df = wsi_inference(
        args.in_file, 
        model,
        frame=args.frame,
        device=args.device,
        max_det=args.max_det,
        iou_thr=args.iou_thr,
        conf_thr=args.conf_thr,
        fill=(0, 0, 0),
        contained_thr=args.contained_thr
    )
    print('Inference complete!')
    
    # Push results to DSA as annotations.
    elements = []

    for _, r in pred_df.iterrows():
        tile_w, tile_h = r.x2 - r.x1, r.y2 - r.y1
        tile_center = [(r.x2 + r.x1) / 2, (r.y2 + r.y1) / 2, 0]

        elements.append({
            'lineColor': 'rgb(0,255,0)',
            'lineWidth': 2,
            'rotation': 0,
            'type': 'rectangle',
            'center': tile_center,
            'width': tile_w,
            'height': tile_h,
            'label': {'value': 'nucleus'},
            'group': 'nucleus'
        })
        
    # Save the annotation as an anot file.
    ann_doc = {
        "name": args.docname, "elements": elements, 
        "description": ""
    }
    
    print('Annotation document setup')
    
    with open(args.tissueAnnotationFile, 'w') as fh:
        json.dump(ann_doc, fh, separators=(',', ':'), sort_keys=False)
        
    print('done')


if __name__ == "__main__":
    # CLI parameters are read from accompanying XML file.
    main(CLIArgumentParser().parse_args())
    # main(parse_args())
