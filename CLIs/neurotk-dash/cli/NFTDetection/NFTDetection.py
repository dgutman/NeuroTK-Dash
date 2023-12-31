# Make neurotk Python module (from dgutman/NeuroTK-Dash repository) available.
import sys
sys.path.append('/opt/scw/NeuroTK-Dash')

from ultralytics import YOLO
from histomicstk.cli.utils import CLIArgumentParser
# from argparse import ArgumentParser
import json
import cv2 as cv
import large_image
import numpy as np
from pathlib import Path
from shapely.geometry import Point, Polygon
from pandas import DataFrame
from libpysal import weights
import networkx as nx

from neurotk.yolo import wsi_inference
from neurotk.yolo.utils import get_devices


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
#         # default=[66357, 43963, 73077, 58981]
#         default=[49084, 39496, 73162, 60590]
#     )
#     parser.add_argument('--device', type=str, default='cuda')
#     parser.add_argument('--max-det', type=int, default=300)
#     parser.add_argument('--iou-thr', type=float, default=0.4)
#     parser.add_argument('--conf-thr', type=float, default=0.2)
#     parser.add_argument('--contained-thr', type=float, default=0.6)
#     parser.add_argument('--mask-thr', type=float, default=0.2)
#     parser.add_argument('--mag', type=int, default=20)
#     parser.add_argument('--docname', type=str, default='NFTs')
#     parser.add_argument('--tissueAnnotationFile', default='annotationFile.json')
#     return parser.parse_args()


def corners_to_polygon(x1: int, y1: int, x2: int, y2: int) -> Polygon:
    """Return a Polygon from shapely with the box coordinates given the top left and bottom right corners of a 
    rectangle (can be rotated).
    
    Args:
        x1, y1, x2, y2: Coordinates of the top left corner (point 1) and the bottom right corner (point 2) of a box.
        
    Returns:
        Shapely polygon object of the box.
        
    """
    return Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])


def main(args):
    """Detect nuclei with pre-trained YOLO model and inference results back
    to the DSA as annotations.
    
    """  
    ts = large_image.getTileSource(args.in_file).getMetadata()
        
    # The FOV is 4mm^2, and since it is square it is 2mm^2 in each side.
    # Note I specifically calculate these for width and height separately,
    # idealy these two mm / pixel resolution is the same on both sides.
    fov_w = int(2 / ts['mm_x'])
    fov_h = int(2 / ts['mm_y'])
    
    # Calculate the radii in pixels at this magnification.
    radii = [150, 200, 250, 300, 400]  # these are in microns
    
    px_radii = [int(r / 1000 / ts['mm_x']) for r in radii]

    # But this is at full resolution, which may or may not be the magnification
    # we are analyzing the image at. Scale down.
    
    # Multiply for full resolution -> low res. mask scale.
    fr_to_mask = args.mask_mag / ts['magnification']
    
    mask = np.zeros(
        (int(ts['sizeY'] * fr_to_mask), int(ts['sizeX'] * fr_to_mask)),
        dtype=np.uint8
    )
    
    """A region can be one or multiple polygons containing the region the 
    analysis. For this workflow this region must be converted into a binary
    mask."""
    print('This is the region info:')
    print('type', type(args.region))
    print(args.region)
    
    if len(args.region) == 4:
        if args.region == [-1, -1, -1, -1]:
            # This signals the whole region!
            mask[:, :] = 255
        else:
            left, top, width, height = args.region
            
            left = int(left * fr_to_mask)
            top = int(top * fr_to_mask)
            width = int(width * fr_to_mask)
            height = int(height * fr_to_mask)
    
            mask[top:top+height, left:left+width] = 255
    else:
        # This is multiple objects or a polygon style region.
        # Regions are separated by two -1, -1 values.
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
    
    # Convert to scale factor in mm^2
    h, w = mask.shape[:2]
    sf = (ts['sizeY'] / h) * (ts['sizeX'] / w)
    sf *= ts['mm_x'] * ts['mm_y']

    # Denominator is the mm^2 area that contains tissue.
    den = np.count_nonzero(mask) * sf
    
    # from shapely import wkt
    # from geopandas import GeoDataFrame
    # from pandas import read_csv
    
    # pred_df = read_csv('temp.csv')
    # pred_df['geometry'] = pred_df['geometry'].apply(wkt.loads)
    # pred_df = GeoDataFrame(pred_df)
    
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
    
    # pred_df.to_csv('temp.csv', index=False)
    print('Inference complete!')
    
    if len(pred_df):    
        # Save some results.
        stats = {}
            
        stats['iNFT_count'] = len(pred_df[pred_df['label'] == 1])
        stats['PreNFT_count'] = len(pred_df[pred_df['label'] == 0])
        
        # Calculate the image features for the WSI.
        stats['Pre-NFT density'] = stats['PreNFT_count'] / den
        stats['iNFT density'] = stats['iNFT_count'] / den
        
        # Find the FOV with the highest density of each type NFT.
        # Convert the geomery to a point.
        for i, r in pred_df.iterrows():
            pred_df.loc[i, 'geometry'] = Point(
                (r.x1 + r.x2) / 2, (r.y1 + r.y2) / 2
            )

        # Check FOVs with some overlap to catch highest FOV.
        xys = []

        for x in range(0, ts['sizeX'], int(fov_w / 2)):
            for y in range(0, ts['sizeY'], int(fov_h / 2)):
                xys.append([x, y])

        # loop for each class
        highest_fov = {0: None, 1: None}

        for cls in (0, 1):
            highest_within = 0
            
            for xy in xys:
                x, y = xy

                # Create the FOV polygon.
                x1, y1, x2, y2 = x, y, x + fov_w, y + fov_h

                fov = corners_to_polygon(x1, y1, x2, y2)

                # Calculate how many points are in the FOV
                within = pred_df[pred_df.within(fov)]
                within = within[within['label'] == cls]

                if len(within) > highest_within:
                    highest_fov[cls] = within.copy()
                    highest_within = len(within)
                    
            if highest_fov[cls] is None:
                highest_fov[cls] = DataFrame(
                    [],
                    columns=['label', 'x1', 'y1', 'x2', 'y2', 'geometry']
                )
                
        stats['Pre-NFT FOV count'] = len(highest_fov[0])
        stats['iNFT FOV count'] = len(highest_fov[1])
        
        # Calculate average clustering cofficient for different radii in the highest FOV!.
        for cls in (0, 1):
            coordinates = []
            
            cls_label = 'iNFT' if cls else 'Pre-NFT'

            for _, r in highest_fov[cls].iterrows():
                coordinates.append([(r.x1 + r.x2) / 2, (r.y1 + r.y2) / 2])
            
            coordinates = np.array(coordinates)
            
            if len(coordinates):
                for i, r in enumerate(px_radii):
                    # https://networkx.org/documentation/stable/auto_examples/geospatial/plot_points.html
                    dist = weights.DistanceBand.from_array(
                        coordinates, threshold=r, silence_warnings=True
                    )

                    dist_graph = dist.to_networkx()

                    # Calculate average clustering of the graph.
                    stats[f'{cls_label} clustering Coef (r={radii[i]})'] = \
                        float(nx.average_clustering(dist_graph))
            else:
                stats[f'{cls_label} clustering Coef (r={radii[i]})'] = 0
    else:
        stats = {
            'iNFT_count': 0,
            'PreNFT_count': 0,
            'Pre-NFT density': 0,
            'iNFT density': 0,
            'Pre-NFT FOV count': 0,
            'iNFT FOV count': 0,
        }
        
        for cls in ('iNFT', 'Pre-NFT'):
            for r in radii:
                stats[f'{cls} clustering Coef (r={r})'] = 0
    
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
        "description": "",
        "attributes": {
            "params": vars(args),
            "stats": stats,
            "cli": Path(__file__).stem,
        }
    }
    
    print('Annotation document setup')
    
    with open(args.tissueAnnotationFile, 'w') as fh:
        json.dump(ann_doc, fh, separators=(',', ':'), sort_keys=False)
        
    print('done')


if __name__ == "__main__":
    # CLI parameters are read from accompanying XML file.
    main(CLIArgumentParser().parse_args())
    # main(parse_args())
