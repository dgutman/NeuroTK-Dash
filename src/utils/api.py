import base64, json

import numpy as np

from PIL import Image
from io import BytesIO
from typing import List
from ..utils.settings import (
    gc,
    MONGODB_DB,
    MONGODB_USERNAME,
    MONGODB_PASSWORD,
    MONGO_URI,
)
from girder_client import GirderClient
import pymongo


## TO REFACTOR.. this should probably be in the settings or config?
mc = pymongo.MongoClient(
    MONGO_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD
)
mc = mc[MONGODB_DB]  ### A


def get_neuroTK_projectDatasets(projectFolderId: str):
    ## Given a projectFolder Id, this needs to find the datasets folder, and then grab metadata
    ## From that...
    for pjf in gc.listFolder(projectFolderId):
        if pjf["name"] == "Datasets":
            ### So the projectFolder should have metadata, and I am specifically looking for
            #  ntkdata_ as the keys..

            dataSetImages = {}
            for k in pjf.get("meta", {}).keys():
                if k.startswith("ntkdata_"):
                    for i in pjf["meta"][k]:
                        dataSetImages[i["_id"]] = i
                        ## TO DO:  JC work on merging the dictionaries instead of overwriting..
                    ## Just return a set of itemId's that are in the project.
            return dataSetImages
            ## Remember this is returning a dictionary, not a list of dictionaries


def get_projects(gc: GirderClient, fld_id: str) -> List[dict]:
    """Get a list of NeuroTK folders for the user.

    Args:
        gc: Girder client.
        fld_id: DSA id of NeuroTK Projects folder.

    Returns:
        List of project metadata.

    """
    # Loop through public and then private folders.
    projects = []

    for fld in gc.listFolder(fld_id):
        for user in gc.listFolder(fld["_id"]):
            for project in gc.listFolder(user["_id"]):
                project["key"] = f"{user['name']}/{project['name']}"
                projects.append(project)

    return projects


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
    try:
        thumb = gc.get(thumb_download_endpoint, jsonResp=False).content
        thumb = np.array(Image.open(BytesIO(thumb)))
        # dropping alpha channel and keeping only rgb
        thumb = thumb[:, :, :3]
    except:
        thumb = np.ones((1000, 1000, 3), dtype=np.uint8)
        # print(thumb)
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

    ## DEBUG POINT LIMIT HERE

    points = f"[{', '.join(points)}]"
    return points


def find_job_record(search_dict):
    # Initialize MongoDB client
    collection = mc["dsaJobQueue"]
    # Prepare the query. You might need to adjust this to your specific needs

    ## TO DO.. figure out why the job Queue elements are making integers into strings..

    ## Need to cast all the values to a string and also add the _original_params to the key
    str_search_dict = {f"_original_params.{k}": str(v) for k, v in search_dict.items()}

    ## KNOWLEDGE:  So the original_params are only returned by the job submission function
    ## IT does not appear these are directly embedded in an actual job Item on the DSA itself..
    ## Neer to verify this behavior with Manthey

    # str_search_dict = {f"_original_params.{k}": v for k, v in search_dict.items()}

    # Search for the record
    matching_record = collection.find_one(str_search_dict)

    if matching_record:
        # print(f"Found a matching record: {matching_record['_id']}")
        return matching_record
    else:
        ## Uncomment to debug job execution
        # print("No matching record found.")
        # print(str_search_dict)
        return None


def run_ppc(data, params, run=False):
    ppc_ext = "slicer_cli_web/dsarchive_histomicstk_latest/PositivePixelCount/run"
    print("Trying to run ppc and call this function.")
    # print(gc.token)
    ## Test point set only running on small ROI to test code
    points = "[5000,5000,1000,1000]"

    maskName = []

    ### NOTE That this is not checking if the image has largeImage set...
    ## This also needs to throw an error

    jobStatus = []
    alreadyRan = []
    for i in data:
        try:
            item = gc.get(f"item/{i['_id']}")

            ### NEED TO THROW AN ERROR PERHAPS IF THE SUBMISSION FAILS?
            ## TO DO

            cliInputData = {
                "inputImageFile": item["largeImage"]["fileId"],  # WSI ID
                "outputLabelImage": f"{item['name']}_ppc.tiff",
                "outputLabelImage_folder": "645a5fb76df8ba8751a8dd7d",
                "outputAnnotationFile": f"{item['name']}_ppc.anot",
                "outputAnnotationFile_folder": "645a5fb76df8ba8751a8dd7d",
                "returnparameterfile": f"{item['name']}_ppc.params",
                "returnparameterfile_folder": "645a5fb76df8ba8751a8dd7d",
            }
            cliInputData.update(params)
            cliInputData["region"] = points
            ## ADD LOGIC HERE TO PREVENT JOBS FROM RERUNNING
            ## Also don't forget to add an override if flag

            # TO DO, can probably combine the streams of submitted vs cached..

            if not find_job_record(cliInputData):
                returned_val = gc.post(ppc_ext, data=cliInputData)
                # print(returned_val)
                jobStatus.append(returned_val)
            else:
                alreadyRan.append(cliInputData)
            # print("-----DATA FOR CLI BELOW----")
            # print(cliInputData)
        except:
            print("Item Failed ..", i)

    print(len(jobStatus), "jobs were submitted..")
    print(len(alreadyRan), "jobs were present in the cache")
    ## FIX HERE... SEE IF THIS WHERE THE JOB STATUS is getting modified

    return jobStatus

    # annotation_name = "gray-matter-fixed"
    annotation_name = "gray-matter-fixed"
    annots = gc.get(f"annotation?text={annotation_name}&limit=0")

    annot_records = {
        annot["_id"]: itemId
        for annot in annots
        if (annot["annotation"]["name"] == annotation_name)
        and ((itemId := annot["itemId"]) in data["Item ID"].values)
    }

    ## Should scan these to look for annotations that are corrupt...

    # retrieve the full annotation details and transform the returned values into a format that is accepted by PPC
    # then run PPC on the item using the annotation bounds as ROI
    for annot_id, item_id in annot_records.items():
        # getting rois from grey matter annotation
        annotation = gc.get(f"annotation/{annot_id}")
        rois = annotation["annotation"]["elements"]

        # transforming the rois into a format that DSA will accept for PPC
        points = get_points(rois)
        print(len(points))
        points = "5000,5000,2000,2000"
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
        print(item)
        if run:
            print(f"RUNNING ITEM: {item_id}")

            # posting the job to DSA and getting the job extension for future reference
            returned_val = gc.post(ppc_ext, data=item)

            job_ext = returned_val["jobInfoSpec"]["url"].split("v1/")[-1]

            # checking job status post-submission
            holder = gc.get(job_ext)
            status = holder["status"]

            # status codes -- 4: fail, 3: success, 0: inactive, 1/2: queued/running
            print(f"STATUS: {status}")
