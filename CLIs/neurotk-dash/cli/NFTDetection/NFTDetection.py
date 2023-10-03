# Make neurotk Python module (from dgutman/NeuroTK-Dash repository) available.
import sys
sys.path.append('/opt/scw/NeuroTK-Dash')

from ultralytics import YOLO
from histomicstk.cli.utils import CLIArgumentParser  # for CLI implementation
import json
import cv2 as cv
import large_image
import numpy as np

from neurotk.yolo import wsi_inference
from neurotk.yolo.utils import get_devices

# from argparse import ArgumentParser  # for developing outside CLI implementation


# def parse_args():
#     """Used for developing and testing script outside of CLI."""
#     parser = ArgumentParser()
    
#     parser.add_argument(
#         '--in-file', type=str,
#         default='/opt/scw/data/2019/E19-100/scanned images/E19-100_1_TAU.svs'
#     )
#     parser.add_argument('--mask-mag', type=float, default=1.25)
#     parser.add_argument(
#         '--region', type=int, nargs='+', 
#         default=[66357, 43963, 73077, 58981]
#     )
#     parser.add_argument('--device', type=str, default='cuda')
#     parser.add_argument('--max-det', type=int, default=300)
#     parser.add_argument('--iou-thr', type=float, default=0.4)
#     parser.add_argument('--conf-thr', type=float, default=0.2)
#     parser.add_argument('--contained-thr', type=float, default=0.6)
#     parser.add_argument('--mask-thr', type=float, default=0.2)
#     parser.add_argument('--mag', type=int, default=20)
#     parser.add_argument('--docname', type=str, default='NFTs')
    
#     return parser.parse_args()


def main(args):
    """Detect nuclei with pre-trained YOLO model and inference results back
    to the DSA as annotations.
    
    """  
    ts = large_image.getTileSource(args.in_file).getMetadata()
    
    # Multiply for full resolution -> low res. mask scale.
    fr_to_mask = args.mask_mag / ts['magnification']
    
    mask = np.zeros(
        (int(ts['sizeY'] * fr_to_mask), int(ts['sizeX'] * fr_to_mask)),
        dtype=np.uint8
    )
    
    # From regions parameter draw a low res mask of the area of anlaysis.
    if len(args.region) == 4:
        left, top, right, bottom = [
            int(coord * fr_to_mask) for coord in args.region
        ]
        mask[top:bottom, left:right] = 255
    else:
        # This is not a single rectangle, convert to contours.
        contours = []
        contour = []

        for coord in args.region:
            if coord < 0:
                if len(contour):
                    contours.append(np.reshape(contour, (-1, 2)))
                    contour = []
            else:
                contour.append(int(coord * fr_to_mask))

        if len(contour):
            contours.append(np.reshape(contour, (-1, 2)))
            
        mask = cv.drawContours(mask, contours, -1, 255, cv.FILLED)
    
    # Get the device ids.
    if args.device == 'cuda':
        # Get the number of devices.
        device = get_devices()[0]
        
        if device is None:
            device = 'cpu'
    elif args.device != 'cpu':
        device = 'cpu'
    else:
        device = 'cpu'
    
    # Load model.
    print('Trying to load YOLO weights')
    model = YOLO('/opt/scw/cli/NFTDetection/best.pt')
    print("YOLO weights loaded.")
    
    print('Inferencing....')
    pred_df = wsi_inference(
        args.in_file, 
        model,
        device=device,
        max_det=args.max_det,
        iou_thr=args.iou_thr,
        conf_thr=args.conf_thr,
        fill=(114, 114, 114),
        contained_thr=args.contained_thr,
        mask_thr=args.mask_thr,
        mask=mask,
        mag=args.mag
    )
    print('Inference complete!')
    
    # Push results to DSA as annotations.
    elements = []

    for _, r in pred_df.iterrows():
        tile_w, tile_h = r.x2 - r.x1, r.y2 - r.y1
        tile_center = [(r.x2 + r.x1) / 2, (r.y2 + r.y1) / 2, 0]
        label = int(r['label'])
        color = 'rgb(255,0,0)' if label else 'rgb(0,0,255)'
        label = 'iNFT' if label else 'Pre-NFT'

        elements.append({
            'lineColor': color,
            'lineWidth': 2,
            'rotation': 0,
            'type': 'rectangle',
            'center': tile_center,
            'width': tile_w,
            'height': tile_h,
            'label': {'value': label},
            'group': label
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
