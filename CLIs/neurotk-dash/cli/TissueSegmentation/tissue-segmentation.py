import sys
sys.path.append('/opt/scw/NeuroTK-Dash')

from histomicstk.cli.utils import CLIArgumentParser
import torch
import large_image
import cv2 as cv
import numpy as np
import json

from neurotk.torch.models import deeplabv3_model
from neurotk.torch.utils import predict_mask
from neurotk.utils import contours_to_points

# from argparse import ArgumentParser


# def parse_args():
#     """Testing arguments being passed"""
#     parser = ArgumentParser()
    
#     parser.add_argument('--in-file', default='/opt/scw/wsis/E20-17_10_AB.svs')
#     parser.add_argument('--size', default=256)
#     parser.add_argument('--thresh', default=0.7)
#     parser.add_argument('--smooth', default=0.1)
#     parser.add_argument('--docname', default='test')
    
#     return parser.parse_args()

def reshape_with_pad(img, size, pad = (255, 255, 255)):
    """Reshape an image into a square aspect ratio without changing the original
    image aspect ratio - i.e. use padding.
    
    """
    h, w = img.shape[:2]

    if w > h:
        img = cv.copyMakeBorder(img, 0, w-h, 0, 0, cv.BORDER_CONSTANT, None, 
                                pad)
    else:
        img = cv.copyMakeBorder(img, 0, 0, 0, h-w, cv.BORDER_CONSTANT, None, 
                                pad)

    # Reshape the image.
    img = cv.resize(img, (size, size), None, None, cv.INTER_NEAREST)

    return img

    
def main(args):
    # Tile source.
    ts = large_image.getTileSource(args.in_file)

    # Get size of WSI.
    ts_metadata = ts.getMetadata()
    w, h = ts_metadata['sizeX'], ts_metadata['sizeY']
    
    print(f'Size of WSI: {w}, {h}')

    # Get thumbnail of image at the desired size.
    kwargs = dict(format=large_image.tilesource.TILE_FORMAT_NUMPY)
    
    if w > h:
        img = ts.getThumbnail(width=args.size, **kwargs)[0][:, :, :3]
    else:
        img = ts.getThumbnail(height=args.size, **kwargs)[0][:, :, :3]
        
    print(f'Original size of thumbnail: {img.shape}')
    lr_h, lr_w = img.shape[:2]
    sf_h, sf_w = h / lr_h, w / lr_w
    
    # Pad the image.
    img = reshape_with_pad(img, args.size, pad=(255, 255, 255))
    
    print(f'Size of thumbnail after reshape: {img.shape}')

    # Load the pretrained model.
    model = deeplabv3_model()
    model.load_state_dict(
        torch.load('/opt/scw/cli/tissue_segmentation/best.pt', 
                   map_location=torch.device('cpu'))
    )
    model.eval()

    pred = predict_mask(model, img, size=args.size, thresh=args.thresh)
    
    print(f'Size of prediction: {pred.shape}')
    
    # Smooth the mask.
    # pred = cv.blur(pred, (args.kernel, args.kernel))
    # pred = (pred > 0).astype(np.uint8) * 255
    
    # Extract contours.
    contours = cv.findContours(pred, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]
    
    # Smoothe the contours
    smoothed_contours = []
    
    for contour in contours:
        smoothed_contours.append(cv.approxPolyDP(contour, args.smooth, True))
    
    # Convert the list of contours to points in DSA format.
    tissue_points = contours_to_points(smoothed_contours)

    # Convert each contour into a list dictionary to pass as an annotation 
    # DSA element.
    tissue_els = []
    
    for pt in tissue_points:
        # Skip a point with too few points*
        # * DSA appears to prevent annotations of three points only.
        if len(pt) < 4:
            continue
            
        # Scale the points
        pt = np.array(pt) 
        print(f'Points shape: {pt.shape}')
        
        pt = pt * [sf_w, sf_h, 1]
        
        pt = pt.astype(int)
        
        tissue_els.append({
            'group': args.docname,
            'type': 'polyline',
            'lineColor': 'rgb(0,179,60)',
            'lineWidth': 4.0,
            'closed': True,
            'points': pt.tolist(),
            'label': {'value': args.docname},
        })

    ann_doc = {
        "name": args.docname, "elements": tissue_els, 
        "description": ""
    }

    with open(args.tissueAnnotationFile, 'w') as fh:
        json.dump(ann_doc, fh, separators=(',', ':'), sort_keys=False)

    
if __name__ == "__main__":
    # CLI parameters are read from accompanying XML file.
    main(CLIArgumentParser().parse_args())
    # main(parse_args())
