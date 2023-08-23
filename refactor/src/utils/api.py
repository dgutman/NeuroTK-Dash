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
from time import sleep
import base64

gc = girder_client.GirderClient(apiUrl=DSA_BASE_Url)
print(gc.authenticate(apiKey=API_KEY))


def get_all_containers():
    holder = []
    for collection in gc.get("/collection?limit=0"):
        collection_id = collection["_id"]

        holder.extend(
            [
                {"item_id": item["_id"], "parent_folder_id": item["folderId"]}
                for item in gc.get(
                    f"resource/{collection_id}/items?type=collection&limit=0"
                )
            ]
        )

    df = pd.DataFrame.from_dict(holder)
    df.drop_duplicates(subset=["parent_folder_id"], inplace=True)

    temp = pd.concat([get_item_path_details(item) for item in df["item_id"].to_list()])
    temp.drop_duplicates(inplace=True)

    filt = temp["item_type"] == "collection"

    temp.loc[filt, "parent_name"] = "Collection"
    temp.loc[~filt, "parent_name"] = temp[~filt].apply(
        (lambda x: temp.loc[temp["_id"] == x["parent_id"], "item_name"].item()), axis=1
    )

    return temp.to_dict(orient="records")


def get_item_path_details(item):
    details = [
        {
            "_id": object_dict["_id"],
            "item_type": object_dict["_modelType"],
            "item_name": object_dict["name"],
            "item_size": object_dict["size"],
            "parent_type": object_dict.get("parentCollection"),
            "parent_id": object_dict.get("parentId"),
        }
        for item in gc.get(f"item/{item}/rootpath")
        if (object_dict := item.get("object", False))
    ]

    return pd.DataFrame(details)


def getItemAnnotations(itemId):
    ### Given an item ID from the DSA, grabs relevant annotation data
    ## This will also have functionality to normalize/cleanup results that are stored in the annotation object
    ## For now I am focusing on pulling out the PPC data
    annotationSet = gc.get(f"annotation?itemId={itemId}")
    # print(annotationSet)
    return annotationSet


def getAllItemAnnotations(annotationName=None):
    ## This grabs/caches all of the annotations that a user has access too.. can be filtered based on annotation Name
    ## This will also have functionality to normalize/cleanup results that are stored in the annotation object
    ## For now I am focusing on pulling out the PPC data
    annotationItemSet = gc.listResource("annotation")
    annotationItemSet = list(annotationItemSet)
    print(
        "You have retrieved %d annotations from the DSA for the current API KEY"
        % len(annotationItemSet)
    )
    return annotationItemSet


def getItemSetData(num_of_items=0):
    # url = f"{DSA_BASE_Url}/resource/{ROOT_FOLDER_ID}/items?type={ROOT_FOLDER_TYPE}&limit={num_of_items}"
    url = (
        f"/resource/{ROOT_FOLDER_ID}/items?type={ROOT_FOLDER_TYPE}&limit={num_of_items}"
    )

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
    thumb_download_endpoint = (
        f"/item/{item_id}/tiles/thumbnail?encoding={encoding}&height={height}"
    )
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

    keep_cols = [
        "index",
        "Created On",
        "NumberStrongPositive",
        "NumberTotalPixels",
        "RatioStrongToPixels",
    ]
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


def get_items_in_container(parent_id, container_type="folder"):
    """Recursively gets items in a folder.

    Args:
        parent_id: The id of the folder to get all items under.
        container_type: Either folder or collection.

    Returns:
        List of items in parent folder.

    """
    return gc.get(
        f"resource/{parent_id}/items?type={container_type}&limit=0&sort=_id&sortdir=1"
    )


def get_folder_items(parent_id):
    """Recursively gets items in a folder.

    Args:
        parent_id: The id of the folder to get all items under.

    Returns:
        List of items in parent folder.

    """
    return gc.get(f"resource/{parent_id}/items?type=folder&limit=0&sort=_id&sortdir=1")


def get_items_in_folder(folder_id):
    metadata = dict()
    items = get_folder_items(folder_id)

    for item in items:
        if not item["meta"]:
            continue

        metadata[item["_id"]] = item["meta"]["npSchema"]

        large_image = (
            l_image
            if (l_image := item.get("largeImage")) is None
            else l_image.get("fileId")
        )

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


def get_ppc_details_specific(
    folder_id,
    daterange,
    keep_regions,
    stains_of_interest,
    ppc_params,
    annotation_name="Positive Pixel Count",
):
    # get all items with annotations which match the provided name
    # using this as a proxy filter to target only relevant images for PPC data aggregation

    original_items = get_items_in_folder(folder_id)

    filt = (original_items["stainID"].isin(stains_of_interest)) & (
        original_items["regionName"].isin(keep_regions)
    )
    original_items = original_items[filt]

    folder_item_count = len(original_items)

    # get all items with annotations which match the provided name
    # using this as a proxy filter to allow removal of any which already have positive pixel count

    annots = gc.get(f"annotation?text={annotation_name}&limit=0")

    ppc_create_date = pd.date_range(start=daterange[0], end=daterange[1])
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
            and (item_id in original_items["item_id"].values)
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

    req_cols = [
        "caseID",
        "stainID",
        "regionName",
        "ABC",
        "Braak Stage",
        "CERAD",
        "Thal",
    ]

    if all([val in metadata_df.columns for val in req_cols]):
        metadata_df = update_metadata_df(metadata_df, ppc_records)

        metadata_df.reset_index(inplace=True)
        metadata_df.rename(
            columns={
                "index": "item_id",
                "RatioStrongToPixels": "Percent Strong Positive",
            },
            inplace=True,
        )

        req_cols.insert(0, "item_id")
        req_cols.insert(2, "Percent Strong Positive")

        metadata_df = metadata_df[req_cols]
        final_item_count = metadata_df.shape[0]

        filt = original_items["item_id"].isin(metadata_df["item_id"])
        absent = original_items[~filt]

        abs_cols = ["item_id", "blockID", "caseID", "regionName", "stainID"]
        absent = absent[abs_cols]

        return metadata_df, absent, (final_item_count, folder_item_count)

    return pd.DataFrame(), pd.DataFrame(), (0, folder_item_count)


def get_points(rois, delineator=["-1, -1"]):
    """
    Takes rois as a list of list of integers and returns them properly formatted for PPC via DSA
    Can also handle cases where rois is a list of dictionaries with a "points" key
    All rois have form [[int, int, int], [int, int, int], ..., [int, int, int]]
    This is true even of those rois stored in a dictionary
    Assumes the points exist in a 2D plane and so only takes the first two values from each sub-list/point
    There are cases where the rois can be of the same from but already be in 2D form (i.e. [int, int])
    The function is not impacted by this difference and will behave the same
    Points are returned as a string representation of the list with each roi delineated by the provided delineator
    """
    points = []
    region_count = len(rois)

    delineate = region_count > 1

    for ind, roi in enumerate(rois, start=1):
        if isinstance(roi, list):
            [points.extend([str(item) for item in val[:2]]) for val in roi]
        else:
            # getting all non-zero points, converting to string and adding to points liste
            [points.extend([str(item) for item in val[:2]]) for val in roi["points"]]

        # don't want to add delineator to the last roi since it doesn't need to be delineated
        if (delineate) and (ind != region_count):
            points.extend(delineator)

    points = f"[{', '.join(points)}]"
    return points


def run_ppc(data, params, run=False):
    ppc_ext = "slicer_cli_web/dsarchive_histomicstk_latest/PositivePixelCount/run"

    # annotation_name = "gray-matter-fixed"
    annotation_name = "gray-matter-fixed"
    annots = gc.get(f"annotation?text={annotation_name}&limit=0")

    annot_records = {
        annot["_id"]: itemId
        for annot in annots
        if (annot["annotation"]["name"] == annotation_name)
        and ((itemId := annot["itemId"]) in data["Item ID"].values)
    }

    # retrieve the full annotation details and transform the returned values into a format that is accepted by PPC
    # then run PPC on the item using the annotation bounds as ROI
    for annot_id, item_id in annot_records.items():
        # getting rois from grey matter annotation
        annotation = gc.get(f"annotation/{annot_id}")
        rois = annotation["annotation"]["elements"]

        # transforming the rois into a format that DSA will accept for PPC
        points = get_points(rois)

        # finally get details of the image/item to run PPC on
        item = gc.get(f"item/{item_id}")

        item = {
            "inputImageFile": item["largeImage"]["fileId"],  # WSI ID
            "outputLabelImage": f"{item['name']}_ppc.tiff",
            "outputLabelImage_folder": "645a5fb76df8ba8751a8dd7d",
            "outputAnnotationFile": f"{item['name']}_ppc.anot",
            "outputAnnotationFile_folder": "645a5fb76df8ba8751a8dd7d",
            "region": points,
            "returnparameterfile": f"{item['name']}_ppc.params",
            "returnparameterfile_folder": "645a5fb76df8ba8751a8dd7d",
        }

        item.update(params)

        if run:
            print(f"RUNNING ITEM: {item_id}")

            # posting the job to DSA and getting the job extension for future reference
            returned_val = gc.post(ppc_ext, data=item)

            job_ext = returned_val["jobInfoSpec"]["url"].split("v1/")[-1]

            sleep(5)

            # checking job status post-submission
            holder = gc.get(job_ext)
            status = holder["status"]

            # status codes -- 4: fail, 3: success, 0: inactive, 1/2: queued/running
            print(f"STATUS: {status}")


# NOTE: below deprecated because it takes ~2 minutes longer on average than the above
# HOWEVER, it may be of value in the future because it gets *ALL* folders and not just
# those which contain items

# def get_all_containers_recursive(temp=False):
#     collections = gc.get("/collection?limit=0")

#     top_folders = []
#     all_collections = []

#     for collection in collections:
#         collection_id = collection["_id"]
#         collection_name = collection["name"]

#         all_collections.append(
#             {
#                 "parent_id": None,
#                 "parent_name": None,
#                 "child_id": collection_id,
#                 "child_name": collection_name,
#                 "item_count": 0,
#             }
#         )

#         top_folders.extend(
#             [
#                 {
#                     "parent_id": collection_id,
#                     "parent_name": collection_name,
#                     "child_id": folder["_id"],
#                     "child_name": folder_name,
#                     "item_count": 0,
#                 }
#                 for folder in gc.get(f"folder?limit=0&parentType=collection&parentId={collection_id}")
#                 if not (folder_name := folder["name"]).startswith(".")
#             ]
#         )

#     deep_folders = []
#     for folder in top_folders:
#         deep_folders.extend(recurse_folders(folder["child_id"], folder["child_name"]))

#     all_collections.extend(top_folders)
#     all_collections.extend(deep_folders)

#     # having to drop duplicates means there may be a bug in here somewhere or I'm not fully understanding
#     # how the back end is organized. It could be the case that say two collections both point to a given folder
#     # which could end up duplicating that folder's contents in this process
#     # if this can be avoided, we can drop the transform to DF, drop duplicates, then transform back to list of dicts
#     # and should also shave off significant I/O wait time, etc.
#     all_collections = pd.DataFrame(all_collections)
#     all_collections.drop_duplicates(inplace=True)

#     if temp:
#         return all_collections

#     return all_collections.to_dict(orient="records")


# @lru_cache(maxsize=None)
# def recurse_folders(parent_id, parent_name):
#     print(parent_id)
#     child_folders = list(gc.get(f"folder?limit=0&parentType=folder&parentId={parent_id}"))

#     if child_folders:
#         recursed = [
#             {
#                 "parent_id": parent_id,
#                 "parent_name": parent_name,
#                 "child_id": folder["_id"],
#                 "child_name": folder_name,
#                 "item_count": 0,
#             }
#             for folder in child_folders
#             if not (folder_name := folder["name"]).startswith(".")
#         ]

#         [
#             recursed.extend(recurse_folders(child_id, val["child_name"]))
#             for val in recursed
#             if ((child_id := val["child_id"]) is not None)
#         ]

#         return recursed

#     else:
#         base_case_data = {
#             "parent_id": parent_id,
#             "parent_name": parent_name,
#             "child_id": None,
#             "child_name": None,
#             "item_count": gc.get(f"/folder/{parent_id}/details")["nItems"],
#         }
#         return [base_case_data]
