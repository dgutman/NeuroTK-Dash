import base64

import numpy as np

from PIL import Image
from io import BytesIO
from typing import List
from ..utils.settings import gc
from girder_client import GirderClient


def get_neuroTK_projectDatasets(projectFolderId: str):
    ## Given a projectFolder Id, this needs to find the datasets folder, and then grab metadata
    ## From that...

    ## We need the Datasets folder and the Tasks folder..

    dataSetsFolder = None
    tasksFolder = None

    for pjf in gc.listFolder(projectFolderId):
        if pjf["name"] == "Datasets":
            dataSetsFolder = pjf
        elif pjf["name"] == "Tasks":
            tasksFolder = pjf

    ## Get the list of items in the tasks folder..

    taskImageIdDict = {}

    for i in gc.listItem(tasksFolder["_id"]):
        taskName = i["name"]
        ## Now get the task..
        taskImageList = i["meta"].get("images", {})
        print(taskName, "has", len(taskImageList), "images in it..")
        if taskImageList:
            taskImageIdDict[taskName] = taskImageList

    dataSetImages = {}
    for k in dataSetsFolder.get("meta", {}).keys():
        if k.startswith("ntkdata_"):
            for i in dataSetsFolder["meta"][k]:
                dataSetImages[i["_id"]] = i
                ## TO DO:  JC work on merging the dictionaries instead of overwriting..
                ## Just return a set of itemId's that are in the project.
    # Now comes the fun datasets logic, where I am going to one_hot_encode all of the taskNames as a new column

    ## This will now add a magical  column telling me what task a given image has been assigned to
    for taskName in taskImageIdDict:
        for imgId in taskImageIdDict[taskName]:
            if imgId in dataSetImages:
                dataSetImages[imgId]["taskAssigned_" + taskName] = 1

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
