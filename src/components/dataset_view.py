from dash import html, dcc, callback, Output, Input, State
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from typing import List
import pandas as pd

from ..utils.database import getProjectDataset
from ..utils.helpers import generate_generic_DataTable
from .imageSetViewer import generate_imageSetViewer_layout
from .dataView_component import generateDataViewLayout

dataset_view = html.Div(
    [
        dcc.Store("filteredItem_store"),
        dcc.Store("projectItem_store"),
        dcc.Store("itemSet-state"),  # Storing itemSet as state
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
                            html.Div(),
                            id="project-itemSet-div",
                        ),
                    ],
                    value="table",
                    id="table_tab_panel",
                ),
                dmc.TabsPanel(
                    [
                        html.Div(
                            id="images_div",
                            children=[
                                dbc.Pagination(
                                    id="pagination",
                                    size="sm",
                                    active_page=1,
                                    max_value=1,
                                ),
                                html.Div(id="cards-container"),
                                dbc.RadioItems(
                                    id="size-selector",
                                    value="small",  # Default value
                                    inline=True,
                                ),
                            ],
                        ),
                    ],
                    value="images",
                    id="images_tab_panel",
                ),
            ],
            orientation="vertical",
            value="images",
        ),
    ]
)


@callback(
    Output("projectItem_store", "data"),
    [Input("projects-dropdown", "value"), Input("projects-dropdown", "data")],
)
def updateProjectItemStore(projectId: str, projectData: List[dict]) -> List[dict]:
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
    Output("filteredItem_store", "data"),
    [Input("projectItem_store", "data"), Input("tasks-dropdown", "value")],
)
def updateFilteredItemStore(projectItemSet, selectedTask):
    ### Update the filteredItemStore based on selected task...
    print(
        len(projectItemSet),
        "items originally, going to to try and filter",
        selectedTask,
    )

    if projectItemSet:
        df = pd.json_normalize(projectItemSet, sep="-")

        # If task is selected then filter by the task.
        if selectedTask:
            taskColName = f"taskAssigned_{selectedTask}"

            if taskColName in df:
                df = df[df[taskColName] == "Assigned"]
            else:
                df = pd.DataFrame()

        # Drop columns with Task Assigned at the beginning.
        cols_to_drop = []

        for col in df.columns.tolist():
            if col.startswith("taskAssigned_"):
                cols_to_drop.append(col)

        df = df.drop(columns=cols_to_drop)
        print(len(df), "should be left after filtering on", selectedTask)
        return df.to_dict("records")


@callback(
    Output("project-itemSet-div", "children"),
    Input("tasks-dropdown", "value"),
    Input("projectItem_store", "data"),
)
def updateProjectItemSetTable(
    selectedTask: str, projectItemSet: List[dict]
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
                df = df[df[taskColName] == "Assigned"]
            else:
                df = pd.DataFrame()

        # Drop columns with Task Assigned at the beginning.
        cols_to_drop = []

        for col in df.columns.tolist():
            if col.startswith("taskAssigned_"):
                cols_to_drop.append(col)

        df = df.drop(columns=cols_to_drop)

        return [generate_generic_DataTable(df, "project-itemSet-table")]

    return [generate_generic_DataTable(pd.DataFrame(), "project-itemSet-table")]


@callback(
    Output("images_div", "children"),
    Input("filteredItem_store", "data"),
)
def updateDataView(projectItemSet):
    ## Update view
    print("Received", len(projectItemSet), "items for data view")

    if projectItemSet:
        imageDataView_panel = generateDataViewLayout(projectItemSet)
        return imageDataView_panel
    return html.Div()
