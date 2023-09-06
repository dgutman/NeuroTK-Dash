"""
Pop up component for adding a new Project.

FILE: create_project_popup.py
"""
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, Output, Input, State, callback, no_update

from ..utils.settings import USER, PROJECTS_ROOT_FOLDER_ID, gc
from ..utils.database import getProjects

create_project_popup = dbc.Modal(
    [
        dbc.ModalHeader('Create Project'),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(
                    dmc.TextInput(
                        id='new-project-name',
                        label='Project name:',
                        placeholder='Input new project name.'
                    )
                )
            ]),
            dbc.Row([
                dmc.Alert('', color='red', id='create-project-alert',
                          hide=True)
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col(
                    dmc.Switch(
                        onLabel='Private',
                        offLabel='Public',
                        size='xl',
                        id='project-type-toggle'
                    )
                ),
                dbc.Col(
                    html.Button(
                        'Create Project',
                        style={'background': '#7df097'},
                        id='create-project-bn',
                        disabled=True
                    )
                ),
            ])
        ])
    ],
    id='create-project-popup',
    is_open=False,
    fullscreen=False
)


@callback(
    Output('create-project-popup', 'is_open'),
    Input('open-create-project-bn', 'n_clicks'),
    prevent_initial_call=False
)
def open_create_project_popup(n_clicks: int):
    """
    Open the window for creating new projects.

    Args:
        n_clicks: Number of times the button to open up the "create projects
            modal" has been clicked.

    Returns:
        None if the button has not been clicked, otherwise returns the input
        n_clicks. 

    """
    return n_clicks
    

@callback(
    Output('create-project-bn', 'disabled'),
    Input('new-project-name', 'value'),
    prevent_initial_call=True
)
def disable_create_project_bn(new_project_name: str):
    """
    Disable the button to create a project when the input field (i.e. the name) 
    is empty.

    Args:
        new_project_name: 

    Returns:
        True if there is text in the input project name text box or False 
        otherwise.
    
    """
    return False if new_project_name else True
    

@callback(
    [
        Output('projects-store', 'data', allow_duplicate=True),
        Output('create-project-popup', 'is_open', allow_duplicate=True),
        Output('create-project-alert', 'hide'),
    ],
    Input('create-project-bn', 'n_clicks'),
    [
        State('projects-store', 'data'),
        State('project-type-toggle', 'checked'),
        State('new-project-name', 'value'),
    ],
    prevent_initial_call=True,
)
def create_new_project(n_clicks, data, state, value):
    """
    Logic for creating a new project.

    """
    # When the create new project button is clicked.
    if n_clicks:
        # Check for new project.
        new_project = f'{USER}/{value}'

        if new_project in [d['key'] for d in data]:
            return data if len(data) else [], True, False
        else:
            # Create the new folder.
            privacy = 'Private' if state else 'Public'

            # Create new project folder.
            type_fld = gc.createFolder(PROJECTS_ROOT_FOLDER_ID, privacy, 
                                       reuseExisting=True)
            
            user_fld = gc.createFolder(type_fld['_id'], USER, 
                                       reuseExisting=True)
            
            # Create the project folder.
            _ = gc.createFolder(user_fld['_id'], value)

            return getProjects(PROJECTS_ROOT_FOLDER_ID, forceRefresh=True), False, True
        
    return data if len(data) else [], False, True


@callback(
    Output('create-project-alert', 'children'),
    Input('create-project-alert', 'hide'),
    State('new-project-name', 'value'),
    prevent_initial_call=True
)
def alert_existing_project(hide, value):
    if hide:
        return ''
    else:
        return f'{USER}/{value} project already exists.'


@callback(
    [
        Output('projects-dropdown', 'value'),
        Output('new-project-name', 'value')
    ],
    Input("projects-store", "data"),
    State('new-project-name', 'value'),
    State('create-project-alert', 'hide'),
    State('projects-dropdown', 'value')
)
def update_dropdown_value(data, value, hide, selected_project):
    """
    Update the value of the project dropdown.
    
    """
    # If there is a value in the new project screen
    if value:
        # The popup must be open for this to count
        if not hide:
            return no_update, value

        for d in data:
            if d['name'] == value:
                return d['_id'], ''

    if len(data):
        return data[0]['_id'], ''
    else:
        return '', ''