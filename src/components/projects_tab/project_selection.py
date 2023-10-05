"""
This div should contain the project selection functionality including the
dropdown menu to select available projects to the user, and the ability to
create new projects via button.
"""
from dash import html, dcc, Output, Input, callback, State, no_update
from dash_mantine_components import Select
import dash_bootstrap_components as dbc

from .create_project_popup import create_project_popup
from ...utils.database import getProjects, getProjectDataset
from ...utils.settings import PROJECTS_ROOT_FOLDER_ID

project_selection = html.Div(
    [
        dcc.Store(id="projects-store", data=" "),
        dcc.Store(id="curProjectName_store"),
        html.Div(id="load-project-store"),
        dbc.Row(
            [
                dbc.Col(
                    html.Button(
                        [html.I(className="fa-solid fa-arrows-rotate")],
                        id="refresh-item-store",
                        style={"background-color": "orange"},
                        title="Refresh current project item store.",
                        disabled=True,
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Button(
                        [html.I(className="fa-solid fa-arrows-rotate")],
                        id="refresh-projects-bn",
                        title="Refresh the availble projects.",
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Div("Select project: ", style={"fontWeight": "bold"}),
                    align="start",
                    width="auto",
                ),
                dbc.Col(
                    Select(
                        data=[],
                        id="projects-dropdown",
                        placeholder="No project selected.",
                    )
                ),
                dbc.Col(
                    html.Div(
                        html.Button(
                            [html.I(className="fa-solid fa-plus")],
                            title="create new project",
                            id="open-create-project-bn",
                        )
                    ),
                    align="end",
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        html.Button(
                            [html.I(className="fa-solid fa-trash")],
                            title="delete selected project",
                            id="delete-project",
                        )
                    ),
                    align="end",
                    width="auto",
                ),
            ]
        ),
        create_project_popup,
    ],
    id="project-selection",
)


@callback(
    Output("refresh-item-store", "disabled"),
    Input("projects-dropdown", "value"),
    prevent_initial_call=True,
)
def refresh_itemStore_state(selected_project):
    """
    Disable the refresh new project button if a project is not selected.

    """
    return False if selected_project else True


@callback(
    Output("projectItem_store", "data", allow_duplicate=True),
    Input("refresh-item-store", "n_clicks"),
    [State("projects-dropdown", "data"), State("projects-dropdown", "value")],
    prevent_initial_call=True,
)
def refresh_projectItem_store(n_clicks, available_projects, project_id):
    """
    Update the project item store.
    """
    if n_clicks:
        # Get the name of the project.
        projectName = None

        for project in available_projects:
            if project["value"] == project_id:
                projectName = project["label"]
                break

        if projectName:
            # Get the project items (images) from the Project folder.
            projectItemSet = getProjectDataset(
                projectName, project_id, forceRefresh=True
            )

            return projectItemSet if projectItemSet else []
        else:
            raise Exception("Could not find the project in the dropdown.")
    else:
        return no_update


@callback(
    Output("projects-store", "data"),
    [Input("load-project-store", "children"), Input("refresh-projects-bn", "n_clicks")],
)
def start_store(_, n_clicks: bool):
    """
    This is a simple trigger function that will initiate store loading.
    """
    return getProjects(PROJECTS_ROOT_FOLDER_ID, forceRefresh=n_clicks)


# Adding current project info to the main top bar
@callback(
    [Output("curProject_disp", "children"), Output("curProjectName_store", "data")],
    [
        Input("projects-dropdown", "value"),
        Input("projects-dropdown", "data"),
    ],
    prevent_initial_call=True,
)
def updateProjectNameStore(projectId, projectData):
    if projectId and projectData:
        for p in projectData:
            if p["value"] == projectId:
                return (
                    html.Div(
                        ["Current project: ", html.Strong(f"{p['label']}")],
                        style={"color": "#fcfcfc"},
                    ),
                    p["label"],
                )
    else:
        return (
            html.Div(
                ["Current project: ", html.Strong("no project selected")],
                style={"color": "#fcfcfc"},
            ),
            "",
        )


@callback(
    Output("projects-dropdown", "data"),
    Input("projects-store", "data"),
)
def populate_projects(data):
    """
    Populate the projects dropdown.
    """
    options = [{"value": project["_id"], "label": project["key"]} for project in data]

    if len(options):
        return options
    else:
        return []
