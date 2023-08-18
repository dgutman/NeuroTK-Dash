"""
This is the div / frame where we will put the project dropdown, create new
project button, task dropdown, create new task button, and the dataset 
components.
"""
from dash import html, Output, Input, State, dcc, callback, no_update
from ..settings import gc

from .project_selection import project_selection
from .task_selection import task_selection
from ..utils.helpers import generate_generic_DataTable
from ..utils.database import upsert_image_records, get_records_with_images, fetch_and_cache_image_thumb
from .imageSetViewer import generate_imageSetViewer_layout, create_card_content

import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

import numpy as np
import pandas as pd

np.random.seed(42)


# NOTE: There's a bug here which seems to allow multiple processes which sync down the image thumbnails to run
# simultaneously. For example, on page load the process begins, but if the user then selects a task from the dropdown
# an identical process kicks off and runs concurrent to the original, identical process
# since the lru_cache is used when pulling the images in the utils file (as base64 thumb), this doesn't have a
# huge performance hit, but it would be ideal if this could be resolved. probably best to have mongo stash
# local copy of the images in the tasks/datasets which have been loaded before and just pull based on "_id"
# and have placeholder/filler for cases where the image isn't already cached and an option to sync images
# either writ large or just those it noticed were missing from the current selection


projects_frame = html.Div(
    [
        project_selection,
        task_selection,
        html.Br(id="no_update_div"),
        dmc.Tabs(
            [
                dmc.TabsList(
                    [
                        dmc.Tab("Table", value="table"),
                        dmc.Tab("Images", value="images"),
                    ]
                ),
                dmc.TabsPanel(
                    [
                        html.Div([dbc.Row(dmc.Loader(size="md", variant="oval"))], id="datatable_div"),
                    ],
                    value="table",
                    id="table_tab_panel",
                ),
                dmc.TabsPanel(
                    [html.Div(id="images_tab_placeholder")],
                    value="images",
                    id="images_tab_panel",
                ),
            ],
            orientation="vertical",
            value="table",
        ),
    ],
    id="projects-frame",
)


@callback(
    [
        Output("datatable_div", "children"),
        Output("images_tab_placeholder", "children"),
    ],
    [
        Input("projects-dropdown", "value"),
        Input("tasks-dropdown", "value"),
    ],
)
def get_item_datatable_and_images(project_id, task):
    if task:
        task_details = gc.getItem(task)
        task_folderId, task_name = task_details["folderId"], task_details["meta"].get("datasets")

        if task_name is None:
            text = "No datasets for this task available"
            return [html.H3(text)], [html.H3(text)]

        task_parentId = gc.getFolder(task_folderId)["parentId"]

        dataset_folderId = [item["_id"] for item in gc.listFolder(task_parentId) if item["name"] == "Datasets"][0]

        items = [
            pd.DataFrame(val["meta"]["data"]) for val in gc.listItem(dataset_folderId) if val["name"] in task_name
        ]
        items = pd.concat(items)

    else:
        dataset_folderId = [item["_id"] for item in gc.listFolder(project_id) if item["name"] == "Datasets"][0]
        items = [pd.DataFrame(val["meta"]["data"]) for val in gc.listItem(dataset_folderId)]
        items = pd.concat(items)

    col_map = {"npSchema.caseID": "caseID", "npSchema.stainID": "stainID", "npSchema.regionName": "regionName"}
    items.rename(columns=col_map, inplace=True)

    # Added for testing the case where some images are cached but others aren't
    # To test this case, comment out or delete the below
    items = items.sample(frac=0.5)

    items.replace({"": None}, inplace=True)

    col_map = {"caseID": "Case ID", "stainID": "Stain ID", "regionName": "Region Name"}
    [items[key].fillna(f"No {val} Value Given", inplace=True) for key, val in col_map.items()]

    datatable = [generate_generic_DataTable(items, f"task_and_project_data_table")]

    items_as_dict = items.to_dict(orient="records")
    images = generate_imageSetViewer_layout(items_as_dict)
    upsert_image_records(items_as_dict)

    interval = dcc.Interval(id="check_image_load_trigger", interval=1000, n_intervals=0)

    return datatable, [images, interval]


@callback(
    [
        Output("no_update_div", "children"),
    ],
    [
        Input("images_tab_panel", "children"),
        Input("task_and_project_data_table", "virtualRowData"),
    ],
    prevent_initial_call=True,
)
def dynamically_load_cached_images(children, virtualRowData):
    data = pd.DataFrame(virtualRowData)
    cached_thumbs = get_records_with_images()

    if cached_thumbs:
        cached = []
        for item in cached_thumbs:
            cached.append(item["_id"])

            @callback(
                [Output(item, "children")],
                [
                    Input("check_image_load_trigger", "n_intervals"),
                    State(item, "id"),
                    State("task_and_project_data_table", "virtualRowData"),
                ],
            )
            def temp_func(n_intervals, id, rowData):
                print("HERE_0")
                name = item["name"]
                thumb = item["thumbnail"]
                stainId = item["stainID"]
                regionName = item["regionName"]
                image_details = f"{regionName.title()}, Stained with {stainId}"

                return [create_card_content(name, thumb, image_details)]

        filt = data["_id"].isin(cached)
        data = data[~filt]

    if not data.empty:
        print("DATA NOT EMPTY")
        for item in data.to_dict(orient="records"):
            print("ALSO HERE")

            @callback(
                [Output(item, "children")],
                [
                    Input("check_image_load_trigger", "n_intervals"),
                    State(item, "id"),
                    State("task_and_project_data_table", "virtualRowData"),
                ],
            )
            def temp_func(n_intervals):
                print("HERE_1")
                thumb = fetch_and_cache_image_thumb(item["_id"])

                name = item["name"]
                stainId = item["stainID"]
                regionName = item["regionName"]
                image_details = f"{regionName.title()}, Stained with {stainId}"

                return create_card_content(name, thumb, image_details)

    return no_update
