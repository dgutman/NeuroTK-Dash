"""
This is the div / frame where we will put the project dropdown, create new
project button, task dropdown, create new task button, and the dataset 
components.
"""
from dash import html, Output, Input, State, callback, dcc
from ..utils.settings import gc

from .project_selection import project_selection
from .task_selection import task_selection
from ..utils.helpers import generate_generic_DataTable
from .imageSetViewer import generate_imageSetViewer_layout
from ..utils.database import getProjectDataset

import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

import pandas as pd


# NOTE: There's a bug here which seems to allow multiple processes which sync down the image thumbnails to run
# simultaneously. For example, on page load the process begins, but if the user then selects a task from the dropdown
# an identical process kicks off and runs concurrent to the original, identical process
# since the lru_cache is used when pulling the images in the utils file (as base64 thumb), this doesn't have a
# huge performance hit, but it would be ideal if this could be resolved. probably best to have mongo stash
# local copy of the images in the tasks/datasets which have been loaded before and just pull based on "_id"
# and have placeholder/filler for cases where the image isn't already cached and an option to sync images
# either writ large or just those it noticed were missing from the current selection

simple_dev_tab = html.Div(
    [
        dbc.Button("Refresh Cache?"),
    ]
)


projects_frame = html.Div(
    [
        project_selection,
        task_selection,
        simple_dev_tab,
        dcc.Store("projectItem_store"),
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
                        html.Div(
                            [dbc.Row(dmc.Loader(size="md", variant="oval"))],
                            id="project-itemSet-table",
                        ),
                    ],
                    value="table",
                    id="table_tab_panel",
                ),
                dmc.TabsPanel(
                    [
                        html.Div(
                            [dbc.Row(dmc.Loader(size="md", variant="oval"))],
                            id="images_div",
                        ),
                    ],
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


### Adding call back function for development purposes

## Note this updates the projectItem_store, which then cna update the datatable itself


@callback(
    Output("projectItem_store", "data"),
    Input("projects-dropdown", "value"),
    Input("projects-dropdown", "data"),
)
def updateProjectItemStore(projectId, projectData):
    ### This updates the projectItem store, this will pull data from mongo and/or girder if not already local
    projectName = None

    if projectData:
        for x in projectData:
            if x["value"] == projectId:
                projectName = x["label"]
        #    print(projectId, projectData, projectName)

    projectItemSet = getProjectDataset(projectName, projectId)
    if projectItemSet:
        return projectItemSet
    else:
        return None


## TO DO: Have it blank out the datatable if there's no data for the project


@callback(
    Output("project-itemSet-table", "children"),
    Input("projectItem_store", "data"),
)
def updateProjectItemSetTable(projectItemSet):
    if projectItemSet:
        return [
            generate_generic_DataTable(
                pd.json_normalize(projectItemSet, sep="-"), "project-itemSet-table"
            ),  ## TO DO?? make the column name mappings prettier?
        ]
    else:
        return [html.Div("No dataset for project")]


@callback(
    Output("images_div", "children"),
    Input("projectItem_store", "data"),
)
def updateProjectItemSetTable(projectItemSet):
    if projectItemSet:
        imageDataView_panel = [generate_imageSetViewer_layout(projectItemSet)]
        return imageDataView_panel


# @callback(
#     [Output("devDiv", "children")],
#     Input("projects-dropdown", "value"),
#     Input("projects-dropdown", "data"),
# )
# def simplifyProjectLoading(projectId, projectData):
#     ### Will call the database and see if there's any data already existing given the projectName
#     ## TO REFACTOR, but basically now have to find the ID for the folder which is in the data

#     projectName = None
#     for x in projectData:
#         if x["value"] == projectId:
#             print(x)
#             projectName = x["label"]
#     print(projectId, projectData, projectName)

#     projectItemSet = getProjectDataset(projectName, projectId)
#     ## Now let's get clever and query our local database, will make it that if the projectFlag returns nothing
#     ## It will get the data from Girder instead...
#     if projectItemSet:
#         return [
#             generate_generic_DataTable(
#                 pd.json_normalize(projectItemSet, sep="-"), "project-itemSet-table"
#             ),  ## TO DO?? make the column name mappings prettier?
#         ]
#     return [html.Div()]


# @callback(
#     [
#         Output("datatable_div", "children"),
#         Output("images_div", "children"),
#     ],
#     [
#         Input("projects-dropdown", "value"),
#         Input("tasks-dropdown", "value"),
#     ],
# )
# def get_item_datatable_and_images(project_id, task):
#     print("I received the following project_id", project_id)
#     if project_id:
#         if task:
#             task_details = gc.getItem(task)
#             task_folderId, task_name = task_details["folderId"], task_details[
#                 "meta"
#             ].get("datasets")

#             if task_name is None:
#                 text = "No datasets for this task available"
#                 return [html.H3(text)], [html.H3(text)]

#             task_parentId = gc.getFolder(task_folderId)["parentId"]

#             dataset_folderId = [
#                 item["_id"]
#                 for item in gc.listFolder(task_parentId)
#                 if item["name"] == "Datasets"
#             ][0]

#             items = [
#                 pd.DataFrame(val["meta"]["data"])
#                 for val in gc.listItem(dataset_folderId)
#                 if val["name"] in task_name
#             ]
#             items = pd.concat(items)

#         else:
#             dataset_folderId = [
#                 item["_id"]
#                 for item in gc.listFolder(project_id)
#                 if item["name"] == "Datasets"
#             ]

#             if dataset_folderId:
#                 dataset_folderId = dataset_folderId[0]
#                 items = [
#                     pd.DataFrame(val["meta"]["data"])
#                     for val in gc.listItem(dataset_folderId)
#                 ]
#                 items = pd.concat(items)

#             else:
#                 text = "No datasets for this project available"
#                 return [html.H3(text)], [html.H3(text)]

#         col_map = {
#             "npSchema.caseID": "caseID",
#             "npSchema.stainID": "stainID",
#             "npSchema.regionName": "regionName",
#         }
#         items.rename(columns=col_map, inplace=True)

#         # Added for testing the case where some images are cached but others aren't
#         # To test this case, comment out or delete the below
#         items = items.sample(frac=0.5)

#         items.replace({"": None}, inplace=True)

#         col_map = {
#             "caseID": "Case ID",
#             "stainID": "Stain ID",
#             "regionName": "Region Name",
#         }
#         [
#             items[key].fillna(f"No {val} Value Given", inplace=True)
#             for key, val in col_map.items()
#         ]

#         datatable = [generate_generic_DataTable(items, f"task_and_project_data_table")]

#         items_as_dict = items.to_dict(orient="records")
#         images = [generate_imageSetViewer_layout(items_as_dict)]

#         return datatable, images
