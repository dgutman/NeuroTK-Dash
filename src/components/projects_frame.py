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

import pandas as pd

projects_frame = html.Div(
    [
        project_selection,
        task_selection,
        html.Br(),
        html.Div(id="data_div"),
    ],
    id="projects-frame",
)


@callback(
    [Output("data_div", "children")],
    [
        Input("projects-dropdown", "value"),
        Input("tasks-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def get_item_datatable(project_id, task):
    if task:
        task_details = gc.getItem(task)
        task_folderId, task_name = task_details["folderId"], task_details["meta"].get("datasets")

        if task_name is None:
            return [[html.H3("No datasets for this task available")]]

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

    return [generate_generic_DataTable(items, f"task_and_project_data_table")]
