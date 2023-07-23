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
def get_ppc_details_simple():
    ppc_str = "Positive Pixel Count"
    annots = gc.get(f"annotation?text={ppc_str}&limit=0")

    ppc_records = dict()

    for annot in annots:
        item_id = annot["itemId"]
        created = annot["created"].split("T")[0]

        annot = json.loads(
            annot["annotation"]["description"]
            .replace("Used params: ", "{'params':")
            .replace("\nResults:", ',"Results":')
            .replace("'", '"')
            .replace("None", "null")
            + "}"
        )
        annot["Results"].update({"Created On": created})
        ppc_records.update({item_id: annot["Results"]})

    ppc_records = pd.DataFrame.from_dict(ppc_records, orient="index")
    ppc_records.reset_index(inplace=True)

    keep_cols = ["index", "Created On", "NumberStrongPositive", "NumberTotalPixels", "RatioStrongToPixels"]
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


def get_folder_items(gc, parent_id):
    """Recursively gets items in a folder.

    Args:
        gc: Authenticated girder client instance.
        parent_id: The id of the folder to get all items under.

    Returns:
        List of items in parent folder.

    """
    return gc.get(f"resource/{parent_id}/items?type=folder&limit=0&sort=_id&sortdir=1")


def get_items_in_folder(gc, folder_id):
    metadata = dict()
    items = get_folder_items(gc, folder_id)

    for item in items:
        if not item["meta"]:
            continue

        metadata[item["_id"]] = item["meta"]["npSchema"]

        large_image = l_image if (l_image := item.get("largeImage")) is None else l_image.get("fileId")

        update_dict = {"folder_id": item["folderId"], "large_image": large_image}
        metadata[item["_id"]].update(update_dict)

    meta_df = pd.DataFrame.from_dict(metadata, orient="index")

    meta_df.reset_index(inplace=True)
    meta_df.rename(columns={"index": "item_id"}, inplace=True)

    return meta_df


def update_metadata_df(metadata_df, records_df):
    records_df.drop_duplicates(subset=["item_id"], inplace=True)
    records_df.set_index(["item_id"], drop=True, inplace=True)

    # narrowing metadata to only those images for which PPC has been performed
    filt = metadata_df.index.isin(records_df.index)
    metadata_df = metadata_df[filt].copy()

    # updating metadata df to include the percentage calculated above
    metadata_df["RatioStrongToPixels"] = None
    metadata_df.update(records_df)

    return metadata_df


# default folder_id is for Dunn study
def get_ppc_details_specific(folder_id="6464e04c6df8ba8751afabb3", annotation_name="Positive Pixel Count"):
    ppc_params = {
        "hue_value": "0.1",
        "hue_width": "0.5",
        "saturation_minimum": "0.2",
        "intensity_upper_limit": f"{197/255}",
        "intensity_weak_threshold": f"{175/255}",
        "intensity_strong_threshold": f"{100/255}",
        "intensity_lower_limit": "0.0",
    }

    # get all items with annotations which match the provided name
    # using this as a proxy filter to target only relevant images for PPC data aggregation

    dunn_items = get_items_in_folder(gc, folder_id)

    filt = dunn_items["stainID"] == "aBeta"
    dunn_items = dunn_items[filt]

    # get all items with annotations which match the provided name
    # using this as a proxy filter to allow removal of any which already have positive pixel count

    annots = gc.get(f"annotation?text={annotation_name}&limit=0")

    ppc_create_date = ["2023-06-22", "2023-07-06", "2023-07-05", "2023-07-04", "2023-07-03"]
    ppc_records, metadata = dict(), dict()

    # filtering for any that were run with the same params
    # NOTE: potential for bug here since item_id is not really unique -- may have multiple PPC with since item_id, though unlikely given filters present, etc.
    for annot in annots:
        details = {
            val.split(": ")[0].replace("'", ""): val.split(": ")[1].replace("'", "")
            for val in annot["annotation"]["description"].split(", ")
            if any([val.replace("'", "").startswith(key) for key in ppc_params.keys()])
        }

        item_id = annot["itemId"]

        if (
            (details == ppc_params)
            and (item_id in dunn_items["item_id"].values)
            and (annot.get("created").split("T")[0] in ppc_create_date)
        ):
            annot = json.loads(
                annot["annotation"]["description"]
                .replace("Used params: ", "{'params':")
                .replace("\nResults:", ',"Results":')
                .replace("'", '"')
                .replace("None", "null")
                + "}"
            )
            ppc_records.update({item_id: annot["Results"]})

            item = gc.get(f"item/{item_id}")
            metadata[item["_id"]] = item["meta"]["npSchema"]

            if item["meta"].get("npClinical", False):
                metadata[item["_id"]].update(item["meta"]["npClinical"])

    ppc_records = pd.DataFrame.from_dict(ppc_records, orient="index")
    ppc_records.reset_index(inplace=True)
    ppc_records.rename(columns={"index": "item_id"}, inplace=True)
    metadata_df = pd.DataFrame.from_dict(metadata, orient="index")

    keep_regions = [
        "Frontal cortex",
        "Temporal cortex",
        "Parietal cortex",
        "Occipital cortex",
        "Cingulate cortex",
        "Insular cortex",
        "Hippocampus",
        "Amygdala",
    ]

    filt = metadata_df["regionName"].isin(keep_regions)
    metadata_df = metadata_df[filt]

    metadata_df = update_metadata_df(metadata_df, ppc_records)

    # removing control slides
    cont_filt = metadata_df["stainID"] == "control"
    metadata_df = metadata_df[~cont_filt]

    metadata_df.reset_index(inplace=True)
    metadata_df.rename(columns={"index": "item_id", "RatioStrongToPixels": "Percent Strong Positive"}, inplace=True)

    keep_cols = [
        "item_id",
        "caseID",
        "Percent Strong Positive",
        "regionName",
        "Braak Stage",
        "CERAD",
    ]

    metadata_df = metadata_df[keep_cols]

    return metadata_df
