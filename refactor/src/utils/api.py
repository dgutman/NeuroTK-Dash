# notes
"""
This file is for creating a requests session so you can securely load in your api key.
We then create a session and add the api key to the header.
Depending on the API you are using, you might need to modify the value `x-api-key`.
"""

# package imports
import os
import requests
import json
import girder_client
import numpy as np
import pandas as pd

# local imports
from .settings import DSA_BASE_Url, ROOT_FOLDER_ID, ROOT_FOLDER_TYPE, API_KEY
from PIL import Image
from io import BytesIO
import base64

### SIGNIFICANT CHANGE TO DO
### NEED TO USE THE girder_client API to pull all of the data instead of requests, makes life much easier

gc = girder_client.GirderClient(apiUrl=DSA_BASE_Url)
print(gc.authenticate(apiKey=API_KEY))


def getItemAnnotations(itemId):
    ### Given an item ID from the DSA, grabs relevant annotation data
    ## This will also have functionality to normalize/cleanup results that are stored in the annotation object
    ## For now I am focusing on pulling out the PPC data
    annotationSet = gc.get(f"annotation?itemId={itemId}")
    print(annotationSet)
    return annotationSet


def getItemSetData(num_of_items=0):
    # url = f"{DSA_BASE_Url}/resource/{ROOT_FOLDER_ID}/items?type={ROOT_FOLDER_TYPE}&limit={num_of_items}"
    url = f"/resource/{ROOT_FOLDER_ID}/items?type={ROOT_FOLDER_TYPE}&limit={num_of_items}"

    # # print(url)
    # response = requests.get(url)
    response = gc.get(url)

    if response:
        return response
    else:
        print("Error:", response.status_code)
        return None


def pull_thumbnail_array(item_id, height=1000, encoding="PNG"):
    """
    Gets thumbnail image associated with provided item_id and with specified height
    The aspect ratio is retained, so the width may not be equal to the height
    Thumbnail is returned as a numpy array, after dropping alpha channel
    Thumbnail encoding is specified as PNG by default
    """
    thumb_download_endpoint = f"/item/{item_id}/tiles/thumbnail?encoding={encoding}&height={height}"
    thumb = gc.get(thumb_download_endpoint, jsonResp=False).content
    thumb = np.array(Image.open(BytesIO(thumb)))
    # dropping alpha channel and keeping only rgb
    thumb = thumb[:, :, :3]
    return thumb


def get_thumbnail_as_b64(item_id=None, thumb_array=False, height=1000, encoding="PNG"):
    """
    If thumb_array provided, just converts, otherwise will fetch required thumbnail array

    Fetches thumbnail image associated with provided item_id and with specified height
    The aspect ratio is retained, so the width may not be equal to the height

    Thumbnail is returned as b64 encoded string
    """

    if not thumb_array:
        thumb_array = pull_thumbnail_array(item_id, height=height, encoding=encoding)

    img_io = BytesIO()
    Image.fromarray(thumb_array).convert("RGB").save(img_io, "PNG", quality=95)
    b64image = base64.b64encode(img_io.getvalue()).decode("utf-8")

    return "data:image/png;base64," + b64image


def get_largeImageInfo(imageId):
    """
    Returns WSI info; tile size, base size, etc.
    """

    liInfo = gc.get(f"item/{imageId}/tiles")
    return liInfo

    # def get_item_wsi_dims(item_id):    details = gc.get(f"/item/{item_id}/tiles/")    return (details["sizeY"], details["sizeX"])


def get_item_rois(item_id, annot_name=None):
    annots = gc.get(f"annotation/item/{item_id}")

    item_records = [
        element
        for annot in annots
        for element in annot["annotation"]["elements"]
        if (annot_name is None) or (annot["annotation"]["name"] == annot_name)
    ]

    return item_records


def get_annotations_of_type(gc, annot_type):
    annots = gc.get(f"annotation?text={annot_type}&limit=0")

    # keep only the annotation's id and the id of the item it is associated with
    # seems to do a fuzzy match, hence the need for 1: 1 match in logic below
    annot_records = {annot["_id"]: annot["itemId"] for annot in annots if annot["annotation"]["name"] == annot_type}

    metadata = dict()

    for annot_id, item_id in annot_records.items():
        annotation = gc.get(f"annotation/{annot_id}")
        rois = annotation["annotation"]["elements"]

        if not rois:
            continue

        # getting points as a filter since there can be multiple annotations of the same type on a given image
        # so want to make sure we get the right ones
        # TODO: replace with get_annotation_from_rois

        points = []
        region_count = len(rois)

        delineate = region_count > 1
        delineator = ["-1, -1"]

        for ind, roi in enumerate(rois, start=1):
            [points.extend([str(item) for item in val[:2]]) for val in roi["points"]]

            if (delineate) and (ind != region_count):
                points.extend(delineator)

        points = f"[{', '.join(points)}]"

        item = gc.get(f"item/{item_id}")
        metadata[item["_id"]] = item["meta"]["npSchema"]

        update_dict = {
            "folder_id": item["folderId"],
            "large_image": item["largeImage"]["fileId"],
            "points": points,
            "elements": rois,
        }
        metadata[item["_id"]].update(update_dict)

    meta_df = pd.DataFrame.from_dict(metadata, orient="index")

    meta_df.reset_index(inplace=True)
    meta_df.rename(columns={"index": "item_id"}, inplace=True)

    return meta_df
