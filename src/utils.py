# Utility functions.
from girder_client import GirderClient
from typing import List

from dash import html
import dash_ag_grid as dag
from .settings import gc
import numpy as np
from PIL import Image
from io import BytesIO
import base64

from functools import lru_cache

# TODO: eventually split this into things which interface with the DSA API and things which generate components for the app


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


def generate_generic_DataTable(df, id_val, col_defs={}, exportable=False):
    col_defs = [{"field": col} for col in df.columns] if not col_defs else col_defs

    dsa_datatable = html.Div(
        [
            dag.AgGrid(
                id=id_val,
                enableEnterpriseModules=True,
                className="ag-theme-alpine-dark",
                defaultColDef={
                    "filter": "agSetColumnFilter",
                    "editable": True,
                    "flex": 1,
                    "filterParams": {"debounceMs": 2500},
                    "floatingFilter": True,
                },
                columnDefs=col_defs,
                rowData=df.to_dict("records"),
                dashGridOptions={"pagination": True},
                columnSize="sizeToFit",
                csvExportParams={
                    "fileName": f"{id_val.replace('-', '_')}.csv",
                }
                if exportable
                else {},
            ),
        ]
    )

    return dsa_datatable


def pull_thumbnail_array(item_id, height=1000, encoding="PNG"):
    """
    Gets thumbnail image associated with provided item_id and with specified height
    The aspect ratio is retained, so the width may not be equal to the height
    Thumbnail is returned as a numpy array, after dropping alpha channel
    Thumbnail encoding is specified as PNG by default
    """
    thumb_download_endpoint = f"/item/{item_id}/tiles/thumbnail?encoding={encoding}&height={height}"
    try:
        thumb = gc.get(thumb_download_endpoint, jsonResp=False).content
        thumb = np.array(Image.open(BytesIO(thumb)))
        # dropping alpha channel and keeping only rgb
        thumb = thumb[:, :, :3]
    except:
        thumb = np.ones((1000, 1000, 3), dtype=np.uint8)
        # print(thumb)
    return thumb


@lru_cache(maxsize=None)
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
