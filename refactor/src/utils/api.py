# notes
"""
This file is for creating a requests session so you can securely load in your api key.
We then create a session and add the api key to the header.
Depending on the API you are using, you might need to modify the value `x-api-key`.
"""

# package imports
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


# NOTE: not super well implemented -- does not filter for dates or particular params or anything
# I had added this filtering for the PPC chart gen code but want to figure out a better way of doing this
# via the DASH UI or similar in order to be more interactive and not hardcode stuff
def get_ppc_details():
    ppc_str = "Positive Pixel Count"
    annots = gc.get(f"annotation?text={ppc_str}&limit=0")

    ppc_records = dict()

    for annot in annots:
        item_id = annot["itemId"]

        annot = json.loads(
            annot["annotation"]["description"]
            .replace("Used params: ", "{'params':")
            .replace("\nResults:", ',"Results":')
            .replace("'", '"')
            .replace("None", "null")
            + "}"
        )
        ppc_records.update({item_id: annot["Results"]})

    ppc_records = pd.DataFrame.from_dict(ppc_records, orient="index")
    ppc_records.reset_index(inplace=True)

    keep_cols = ["index", "NumberStrongPositive", "NumberTotalPixels", "RatioStrongToPixels"]
    ppc_records = ppc_records[keep_cols]

    ppc_records.rename(
        columns={
            "index": "item_id",
            "NumberStrongPositive": "Count Strong Positive",
            "NumberTotalPixels": "Count Total Pixels",
            "RatioStrongToPixels": "Percent Strong Positive",
        },
        inplace=True,
    )
    return ppc_records
