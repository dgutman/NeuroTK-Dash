import base64

import numpy as np

from PIL import Image
from io import BytesIO
from typing import List
from ..utils.settings import gc
from girder_client import GirderClient


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
                taskImageIdDict[i['name']] = taskImageList

    # Get a list of images in the project dataset.
    # Since there may be multiple datasets make sure to merge dictionaries
    # from duplicate images.
    dataSetImages = {}

    if dataSetsFolder is not None:
        for k in dataSetsFolder.get("meta", {}):
            if k.startswith("ntkdata_"):
                for i in dataSetsFolder["meta"][k]:
                    if i['_id'] not in dataSetImages:
                        dataSetImages[i['_id']] = {}

                    dataSetImages[i["_id"]].update(i)

    # For each unique task, pass a key, value pair to the image information 
    # to assign the task to that image, start the key with "taskAssigned_".
    for taskName, imgIds in taskImageIdDict.items():
        for imgId in imgIds:
            if imgId in dataSetImages:
                dataSetImages[imgId]["taskAssigned_" + taskName] = True
            else:
                dataSetImages[imgId]["taskAssigned_" + taskName] = False

    if dataSetImages:
        return dataSetImages
    ## Remember this is returning a dictionary, not a list of dictionaries
    return None


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
