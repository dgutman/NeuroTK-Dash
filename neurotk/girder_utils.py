# Functions using girder client.
from girder_client import GirderClient, HttpError
from typing import List, Tuple
import numpy as np
from PIL import Image
from io import BytesIO
import cv2 as cv
from .contours_utils import get_contours_from_annotations, scale_contours


def get_annotations_documents(
    gc: GirderClient, item_id: str, doc_names: str | List[str] = None, 
    groups: str | List[str] = None
) -> List[dict]:
    """Get Histomics annotations for an image.
    
    Args:
        gc: Girder client.
        item_id: Item id.
        doc_names: Only include documents with given names.
        groups : Only include annotation documents that contain at least one
            annotation of these set of groups.
       
    Returns:
        List of annotation documents.
     
    """
    if isinstance(doc_names, str):
        doc_names = [doc_names]

    if isinstance(groups, str):
        groups = [groups]
    
    annotation_docs = []
    
    # Get information about annotation documents for item. 
    for doc in gc.get(f'annotation?itemId={item_id}'):
        # If needed only keep documents of certain names.
        if doc_names is not None and \
           doc['annotation']['name'] not in doc_names:
               continue
                
        # Filter out documents with no annotation groups.
        if 'groups' not in doc or not len(doc['groups']):
            continue
            
        # Ignore document if it does not contain elements in the group list.
        if groups is not None:
            ignore_flag = True
            
            for group in doc['groups']:
                if group in groups:
                    ignore_flag = False
                    break
            
            if ignore_flag:
                continue
                
        # Get the full document with elements.
        doc = gc.get(f"annotation/{doc['_id']}")

        # Filter document for elements in group only.
        elements_kept = []
        doc_groups = set()
        
        for element in doc['annotation']['elements']:
            # Remove element without group.
            if 'group' not in element:
                continue
            
            if groups is None or element['group'] in groups:
                elements_kept.append(element)
                doc_groups.add(element['group'])
                    
        doc['groups'] = list(doc_groups)
        doc['annotation']['elements'] = elements_kept
            
        # Add doc if there were elements.
        if len(elements_kept):
            annotation_docs.append(doc)
        
    return annotation_docs


def get_tile_metadata(gc: GirderClient, item_id: str) -> dict:
    """Get the tile source metadata for an item with a large image 
    associated with it.
    
    Args:
        gc: Girder client.
        item_id: DSA WSI id.
    
    Returns:
        Metadata for large image associated.
    
    """
    return gc.get(f'item/{item_id}/tiles')


def get_thumbnail(gc: GirderClient, item_id: str, shape: (int, int) = None,
    fill: (int, int, int) = None) -> np.array:
    """Get thumbnail image of WSI and a binary mask from annotations.
    
    Args:
        gc: Girder client.
        item_id: DSA WSI id.
        shape: Width x height of thumbnail returned. If fill is not 
            specified then width is prioritized to keep same aspect ratio
            of WSI.
        fill: RGB fill to return thumbnail in the exact same aspect ratio
            of shape parameter.

    Returns:
        Thumbnail image and binary mask.
    
    """      
    # Get thumbnail image.
    request = f'item/{item_id}/tiles/thumbnail?'

    if shape is not None:
        request += f'width={shape[0]}&height={shape[1]}'

    if fill is not None:
        request += f'&fill=rgb({fill[0]}%2C{fill[1]}%2C{fill[2]})'

    request += '&encoding=PNG'

    thumbnail = np.array(Image.open(BytesIO(
        gc.get(request, jsonResp=False).content
    )))

    return thumbnail


def get_items(gc: GirderClient, parent_id: str) -> List[dict]:
    """Recursively gets items in a collection or folder parent location.
    
    Args:
        gc: Girder client.
        parent_id: Folder or collection id.
    
    Returns:
        items: Items
        
    """
    try:
        items = gc.get(
            f'resource/{parent_id}/items?type=collection&limit=0&sort=' + \
            '_id&sortdir=1'
        )
    except HttpError:
        items = gc.get(
            f'resource/{parent_id}/items?type=folder&limit=0&sort=_id&' + \
            'sortdir=1'
        )

    return items


def get_thumbnail_with_mask(
    gc: GirderClient, item_id: str, size: int,
    annotation_docs: str | Tuple[str] = None, 
    annotation_groups: str | Tuple[str] = None,
    fill: (int, int, int) = (255, 255, 255)
) -> (np.array, np.array):
    """Get thumbnail image of WSI and a binary mask from annotations.
    Returns the image in square aspect ratio, padding with RGB.
    
    Args:
        gc: Girder client.
        item_id: DSA WSI id.
        size: Size of thumbnail returned.
        annotation_docs: Filter to annotation documents of this name / these 
            names.
        annotation_groups: Filter to annotations from this group / these 
            groups.
        fill: RGB fill when specifying both width and height of different
            aspect ratio than WSI.

    Returns:
        Thumbnail image and binary mask.
    
    """
    # Get thumbnail image.
    thumbnail = get_thumbnail(gc, item_id, shape=(size, size))

    # Annotation documents.
    annotation_docs = get_annotations_documents(
        gc, item_id, doc_names=annotation_docs, 
        groups=annotation_groups
    )

    # Extract annotation elements as contours.
    contours = get_contours_from_annotations(annotation_docs)

    # Get shape of the WSI.
    tile_metadata = get_tile_metadata(gc, item_id)
    
    # Downscale contours to thumbnail size.
    mask = np.zeros(thumbnail.shape[:2], dtype=np.uint8)
    sf = mask.shape[1] / tile_metadata['sizeX']
    
    contours = scale_contours(contours, sf)

    # Draw the contours on mask.
    mask = cv.drawContours(mask, contours, -1, 255, cv.FILLED)

    # Pad the image to be the right shape.
    h, w = mask.shape[:2]

    thumbnail = cv.copyMakeBorder(
        thumbnail, 0, size - h, 0, size - w, cv.BORDER_CONSTANT, 
        value=fill
    )
    mask = cv.copyMakeBorder(
        mask, 0, size - h, 0, size - w, cv.BORDER_CONSTANT, value=0
    )

    return thumbnail, mask


def get_collection(gc: GirderClient, collection_name: str) -> dict:
    """Get DSA collection by name.
    
    Args:
        gc: Girder client.
        collection_name: Name of collection.
        
    Returns:
        DSA metadata.
        
    """
    for collection in gc.get(f'collection?text={collection_name}&limit=50'):
        if collection['name'] == collection_name:
            return collection

        
def lookup_resource(gc: GirderClient, path: str, 
                    resource_type: str = 'collection') -> dict | None:
    """
    Lookup a resource by given path. You can lookup a collection, folder, or
    user with this function.
    
    Args:
        gc: Girder client.
        path: Absolute DSA path to folder or collection (always start with 
            collection for folders) or user to look up if resource_type is user.
        resource_type: If looking for user set to "user" otherwise set to 
            "collection".
            
    Returns:
        Metadata dictionary for collection, folder, or user or None if not
        found.
    
    """
    if resource_type not in ('user', 'collection'):
        raise ValueError(f'Resource type should be "user" or "collection".')
    
    try:
        return gc.get(f'resource/lookup?path=%2F{resource_type}%2F{path}')
    except HttpError:
        return None