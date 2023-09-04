import base64
import numpy as np
import json

from PIL import Image
from io import BytesIO
from typing import List
from ..utils.settings import gc, dbConn
from girder_client import GirderClient, HttpError


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


def get_neuroTK_projectDatasets(projectFolderId: str):
    """
    Get all datasets from a project.

    Args:
        projectFolderId: DSA id of project folder.
    """
    # Find the project "Datasets" and "Tasks" folder.
    dataSetsFolder = None
    tasksFolder = None

    for pjf in gc.listFolder(projectFolderId):
        if pjf["name"] == "Datasets":
            dataSetsFolder = pjf
        elif pjf["name"] == "Tasks":
            tasksFolder = pjf

    # For any current tasks, find the list of image ids.
    taskImageIdDict = {}  # keys: task name, values: list of image ids

    if tasksFolder is not None:
        for i in gc.listItem(tasksFolder["_id"]):
            # Get list of images in task item from metadata.
            taskImageList = i["meta"].get("images", {})

            if taskImageList:
                taskImageIdDict[i["name"]] = taskImageList

    # Get a list of images in the project dataset.
    # Since there may be multiple datasets make sure to merge dictionaries
    # from duplicate images.
    dataSetImages = {}

    if dataSetsFolder is not None:
        for k in dataSetsFolder.get("meta", {}):
            if k.startswith("ntkdata_"):
                for i in dataSetsFolder["meta"][k]:
                    if i["_id"] not in dataSetImages:
                        dataSetImages[i["_id"]] = {}

                    dataSetImages[i["_id"]].update(i)

    # For each unique task, pass a key, value pair to the image information
    # to assign the task to that image, start the key with "taskAssigned_".
    for taskName, imgIds in taskImageIdDict.items():
        for imgId in imgIds:
            if imgId in dataSetImages:
                dataSetImages[imgId]["taskAssigned_" + taskName] = "Assigned"

    if dataSetImages:
        return dataSetImages

    ## Remember this is returning a dictionary, not a list of dictionaries
    return None


def get_projects(gc: GirderClient, fld_id: str) -> List[dict]:
    """Get a list of NeuroTK folders for the userf.

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


def lookup_resource(gc: GirderClient, path: str, resource_type: str = "collection"):
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
    if resource_type not in ("user", "collection"):
        raise ValueError(f'Resource type should be "user" or "collection".')

    try:
        return gc.get(f"resource/lookup?path=%2F{resource_type}%2F{path}")
    except HttpError:
        return None


def get_datasets_list() -> List[dict]:
    """
    Get a list of datasets available to your user.

    Returns:
        List of dataset item information from the DSA. Includes a path key that
        is the username/dataset-name.

    """
    dataset_flds = [
        lookup_resource(gc, "NeuroTK/Datasets/Private"),
        lookup_resource(gc, "NeuroTK/Datasets/Public"),
    ]

    datasets = []

    for fld in dataset_flds:
        if fld:
            # Loop through user folders.
            for user_fld in gc.listFolder(fld["_id"]):
                for dataset_fld in gc.listItem(user_fld["_id"]):
                    dataset_fld["path"] = f"{user_fld['name']}/{dataset_fld['name']}"

                    datasets.append(dataset_fld)

    return datasets


### Adding job import here


def lookup_job_record(search_dict):
    # Initialize MongoDB client
    collection = dbConn["dsaJobQueue"]
    # Prepare the query. You might need to adjust this to your specific needs

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


def submit_ppc_job(data, params):
    ppc_ext = "slicer_cli_web/dsarchive_histomicstk_latest/PositivePixelCount/run"
    # print(gc.token)
    ## Test point set only running on small ROI to test code
    points = "[5000,5000,1000,1000]"

    item = gc.get(f"item/{data['_id']}")
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
    if not lookup_job_record(cliInputData):
        jobSubmission_response = gc.post(ppc_ext, data=cliInputData)
        ## Should I add the userID here as well?
        dbConn["dsaJobQueue"].insert_one(jobSubmission_response)
        return {"status": "SUBMITTED", "girderResponse": jobSubmission_response}

    else:
        # print("Job  was already submitted")
        return {"status": "CACHED"}
