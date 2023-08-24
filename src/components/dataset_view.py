from dash import html, dcc, callback, Output, Input
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from typing import List
import pandas as pd

from ..utils.database import getProjectDataset
from ..utils.helpers import generate_generic_DataTable
from .imageSetViewer import generate_imageSetViewer_layout

dataset_view = html.Div([
    dcc.Store("projectItem_store"),
    dmc.Tabs([
        dmc.TabsList([
            dmc.Tab("Table", value="table"),
            dmc.Tab("Images", value="images"),
        ]),
        dmc.TabsPanel([
            html.Div(
                html.Div(),
                id="project-itemSet-div",
            ),
        ], value="table", id="table_tab_panel"),
        dmc.TabsPanel([
            html.Div(
                html.Div(),
                id="images_div",
            ),
        ], value="images", id="images_tab_panel")
    ], orientation="vertical", value="table")
])


@callback(
    Output("projectItem_store", "data"),
    [
        Input("projects-dropdown", "value"),
        Input("projects-dropdown", "data")
    ]
)
def updateProjectItemStore(
    projectId: str, projectData: List[dict]
) -> List[dict]:
    """
    Updates the projects item store / mongo database when dropdown changes.

    Args:
        projectId: DSA folder id of selected project (from dropdown).
        projectData: All values on the projects dropdown.

    Returns:
        List of dictionaries with item / image metadata.
    
    """
    # Get the name of the project.
    projectName = None

    for x in projectData:
        if x["value"] == projectId:
            projectName = x["label"]
            break

    # Get the project items (images) from the Project folder.
    projectItemSet = getProjectDataset(projectName, projectId, forceRefresh=True)

    if projectItemSet:
        return projectItemSet
    else:
        return []
    

@callback(
    Output("project-itemSet-div", "children"),
    [
        Input("projectItem_store", "data"),
        Input("tasks-dropdown", "value")
    ]
)
def updateProjectItemSetTable(
    projectItemSet: List[dict], selectedTask: str
) -> html.Div:
    """
    Update the contents of the datatable when project store changes (i.e. when
    the projects dropdown changes) or when the task dropdown changes.

    Args:
        projectItemSet: Projet item information which is a list of dictionaries.
        selectedTask: Value of the task dropdown.
    
    Returns:
        Datatable HTML div.
    
    """
    # If there are items read them into dataframe.
    if projectItemSet:
        df = pd.json_normalize(projectItemSet, sep="-")

        # If task is selected then filter by the task.
        if selectedTask:
            taskColName = f"taskAssigned_{selectedTask}"

            if taskColName in df:
                df = df[df[taskColName] == 'Assigned']
            else:
                df = pd.DataFrame()

        # Drop columns with Task Assigned at the beginning.
        cols_to_drop = []

        for col in df.columns.tolist():
            if col.startswith('taskAssigned_'):
                cols_to_drop.append(col)

        df = df.drop(columns=cols_to_drop)

        return [generate_generic_DataTable(df, "project-itemSet-table")]

    return [generate_generic_DataTable(pd.DataFrame(), "project-itemSet-table")]


@callback(
    Output("images_div", "children"),
    Input("projectItem_store", "data"),
)
def updateDataView(projectItemSet):
    ## Update view
    if projectItemSet:
        print('Updating data view...')
        imageDataView_panel = [generate_imageSetViewer_layout(projectItemSet)]
        return imageDataView_panel
    return html.Div()
