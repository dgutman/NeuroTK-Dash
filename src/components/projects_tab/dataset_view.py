from dash import html, dcc, callback, Output, Input, State
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from typing import List
import pandas as pd
import dash_ag_grid as dag

from ...utils.database import getProjectDataset
from ...utils.helpers import generate_generic_DataTable
from ...utils.settings import gc
from ...utils.api import get_datasets_list

from .dataView_component import generateDataViewLayout
from .add_dataset_popup import add_dataset_popup


dataset_view = html.Div(
    [
        dcc.Store("filteredItem_store"),
        dcc.Store("projectItem_store"),
        dcc.Store("dataset-item-store", data=get_datasets_list()),
        dmc.Tabs(
            [
                dmc.TabsList(
                    [
                        dmc.Tab("Table", value="table"),
                        dmc.Tab("Images", value="images"),
                        html.Button(
                            "+ Dataset",
                            id="add-dataset",
                            title="Add dataset",
                            style={"background": "#7df097"},
                        ),
                    ]
                ),
                dmc.TabsPanel(
                    html.Div(
                        dcc.Loading(
                            id='project-itemSet-div', 
                            children=[dag.AgGrid(id="project-itemSet-table")], 
                            type='circle'
                        )
                    ),
                    value="table",
                    id="table_tab_panel"
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
            value="table",
        ),
        add_dataset_popup,
    ]
)


@callback(
    Output("projectItem_store", "data"),
    [Input("projects-dropdown", "value"), Input("add-dataset-bn", "n_clicks")],
    [
        State("projects-dropdown", "data"),
        State("projects-store", "data"),
        State("dataset-dropdown", "value"),
        State("dataset-item-store", "data"),
    ],
    prevent_initial_call=True,
)
def updateProjectItemStore(
    projectId: str,
    n_clicks: int,
    projectData: List[dict],
    projectStore: List[dict],
    dataset: str,
    datasetStore: List[dict],
) -> List[dict]:
    """
    Updates the projects item store / mongo database when dropdown changes.

    Args:
        projectId: DSA folder id of selected project (from dropdown).
        projectData: All values on the projects dropdown.

    Returns:
        List of dictionaries with item / image metadata.

    """
    if projectId:
        # Update project "add dataset button" was clicked.
        if n_clicks:
            refresh_mongo = True

            # Get the dataset selected to add.
            meta = {}

            for dst in datasetStore:
                if dst["_id"] == dataset:
                    meta[f"ntkdata_{dst['name']}"] = dst["meta"]["data"]

            # Get the current project info.
            if meta:
                for project in projectStore:
                    if project["_id"] == projectId:
                        # List the Datasets folders.
                        flds = {
                            fld["name"]: fld
                            for fld in list(gc.listFolder(project["_id"]))
                        }

                        if "Datasets" not in flds:
                            fld = gc.createFolder(projectId, "Datasets")
                        else:
                            fld = flds["Datasets"]

                        _ = gc.addMetadataToFolder(fld["_id"], metadata=meta)
        else:
            refresh_mongo = False

        # Get the name of the project.
        projectName = None

        for x in projectData:
            if x["value"] == projectId:
                projectName = x["label"]
                break

        # Get the project items (images) from the Project folder.
        projectItemSet = getProjectDataset(
            projectName, projectId, forceRefresh=refresh_mongo
        )

        if projectItemSet:
            return projectItemSet
        else:
            return []
    else:
        return []


@callback(
    Output("project-itemSet-div", "children"),
    [Input("tasks-dropdown", "value"), Input("projectItem_store", "data")],
    prevent_initial_call=True,
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
        df = pd.json_normalize(projectItemSet)

        # If task is selected then filter by the task.
        if selectedTask:
            taskColName = f"taskAssigned_{selectedTask}"

            if taskColName in df:
                df = df[df[taskColName] == "Assigned"]

        # Drop columns with Task Assigned at the beginning.
        cols_to_drop = []

        for col in df.columns.tolist():
            if col.startswith("taskAssigned_"):
                cols_to_drop.append(col)

        df = df.drop(columns=cols_to_drop)

        return [generate_generic_DataTable(df, "project-itemSet-table")]

    return [generate_generic_DataTable(pd.DataFrame(), "project-itemSet-table")]


@callback(
    Output("filteredItem_store", "data"),
    Input("project-itemSet-table", "filterModel"),
    State("project-itemSet-table", "virtualRowData"),
    prevent_initial_call=True,
)
def updateFilteredItemStore(filterModel, virtualRowData):
    # We update the filtered item store from changes to the table.
    if virtualRowData is not None and len(virtualRowData):
        return virtualRowData

    return []


@callback(
    Output("images_div", "children"),
    Input("filteredItem_store", "data"),
    prevent_initial_call=True,
)
def updateDataView(projectItemSet):
    ## Update view
    if projectItemSet:
        imageDataView_panel = generateDataViewLayout(projectItemSet)
        return imageDataView_panel
    return html.Div()
