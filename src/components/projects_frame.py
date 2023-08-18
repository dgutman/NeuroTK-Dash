"""
This is the div / frame where we will put the project dropdown, create new
project button, task dropdown, create new task button, and the dataset 
components.
"""
from dash import html, Output, Input, callback, State
from ..settings import gc

from .project_selection import project_selection
from .task_selection import task_selection
from ..utils import generate_generic_DataTable
from .imageSetViewer import generate_imageSetViewer_layout

import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

import pandas as pd


projects_frame = html.Div(
    [
        project_selection,
        task_selection,
        html.Br(),
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
                        html.Div([dbc.Row(dmc.Loader(size="md", variant="oval"))], id="data_div"),
                    ],
                    value="table",
                    id="table_tab_panel",
                ),
                dmc.TabsPanel(
                    [dbc.Row(dmc.Loader(size="md", variant="oval"))],
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
        Output("data_div", "children"),
        Output("images_tab_panel", "children"),
    ],
    [
        Input("projects-dropdown", "value"),
        Input("tasks-dropdown", "value"),
    ],
    prevent_initial_call=True,
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

    items.replace({"": None}, inplace=True)

    col_map = {"caseID": "Case ID", "stainID": "Stain ID", "regionName": "Region Name"}
    [items[key].fillna(f"No {val} Value Given", inplace=True) for key, val in col_map.items()]

    datatable = [generate_generic_DataTable(items, f"task_and_project_data_table")]
    images = [generate_imageSetViewer_layout(items.to_dict(orient="records"))]

    # return datatable, [[]]
    return datatable, images
