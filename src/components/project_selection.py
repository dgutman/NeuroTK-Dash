"""
This div should contain the project selection functionality including the
dropdown menu to select available projects to the user, and the ability to
create new projects via button.
"""
from dash import html, dcc, Output, Input, callback, State
from dash_mantine_components import Select
import dash_bootstrap_components as dbc

from .create_project_popup import create_project_popup
from ..utils.api import get_projects
from ..utils.settings import gc, PROJECTS_ROOT_FOLDER_ID, USER

project_selection = html.Div(
    [
        dcc.Store(
            id="projects-store",
            # data=get_projects(gc, PROJECTS_ROOT_FOLDER_ID),
        ),
        html.Div(id='load-project-store'),
        dbc.Row(
            [
                dbc.Col(
                    html.Div("Select project: ", style={"fontWeight": "bold"}),
                    align="start",
                    width="auto",
                ),
                dbc.Col(Select(
                    data=[], id="projects-dropdown", 
                    placeholder='No project selected.'
                )),
                dbc.Col(
                    html.Div(
                        html.Button(
                            [html.I(className="fa-solid fa-plus")],
                            title="create new project",
                            id='open-create-project-bn'
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
        create_project_popup
    ],
    id="project-selection",
)


@callback(
    Output('projects-store', 'data'),
    Input('load-project-store', 'children')
)
def start_store(_):
    """
    This is a simple trigger function that will initiate store loading.
    """
    return get_projects(gc, PROJECTS_ROOT_FOLDER_ID)


@callback(
    Output("projects-dropdown", "data"),
    Input("projects-store", "data"),
)
def populate_projects(data):
    """
    Populate the projects dropdown.
    """    
    options = [
        {"value": project["_id"], "label": project["key"]} for project in data
    ]

    if len(options):
        return options
    else:
        return []
