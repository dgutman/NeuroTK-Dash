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
from ...utils.settings import PROJECTS_ROOT_FOLDER_ID, USER, COLORS

project_selection = html.Div(
    [
        dcc.Store(id="projects-store", data=" "),
        dcc.Store(id="curProjectName_store"),
        html.Div(id="load-project-store"),
        dbc.Row(
            [
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
                        dbc.Button(
                            "Create project",
                            id="open-create-project-bn",
                            color="success",
                            className="me-1",
                        )
                    ),
                    align="end",
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        dbc.Button(
                            "Delete selected project",
                            id="delete-project",
                            color="danger",
                            className="me-1",
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
    style={"backgroundColor": COLORS["background-secondary"]},
)


@callback(
    Output("projects-store", "data"),
    Input("load-project-store", "children"),
)
def start_store(_):
    """
    This is a simple trigger function that will initiate store loading.
    """
    return getProjects(PROJECTS_ROOT_FOLDER_ID, forceRefresh=False)


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
    names = [project["key"] for project in data]
    data_dict = {
        project["key"]: {"value": project["_id"], "label": project["key"]}
        for project in data
    }

    user_names = []
    other_names = []

    for name in names:
        if name.startswith(USER):
            user_names.append(name)
        else:
            other_names.append(name)

    user_names = sorted(user_names)
    other_names = sorted(other_names)

    options = [data_dict[name] for name in user_names + other_names]

    # Sort with users first.
    if len(options):
        return options
    else:
        return []


@callback(
    Output("projects-dropdown", "value"),
    Input("projects-dropdown", "data"),
    State("new-project-name", "value"),
    suppress_initia_call=True,
)
def change_selected_project(projects, new_project_name):
    """
    Projects is a list of dictionaries, with each dictionary have this structure:
        {'value': a DSA id for the project, 'label': user/projectName}

    """
    if len(projects):
        if new_project_name:
            # There may be a new project created, automatically select it!
            for project in projects:
                if f"{USER}/{new_project_name}" == project["label"]:
                    return project["value"]

        return projects[0]["value"]
    else:
        return ""
