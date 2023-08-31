"""
Pop up component for adding a new Project.

FILE: create_project_popup.py
"""
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, Output, Input, State, callback

from ..utils.settings import USER, PROJECTS_ROOT_FOLDER_ID, gc
from ..utils.api import get_projects

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
    prevent_initial_call=True
)
def open_create_project_popup(n_clicks):
    """
    
    """
    if n_clicks:
        return True
    

@callback(
    [
        Output('projects-store', 'data'),
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
    Create a new project.
    """
    if n_clicks:
        # Check list of project names
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

            return get_projects(gc, PROJECTS_ROOT_FOLDER_ID), False, True
        
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
    Output('create-project-bn', 'disabled'),
    Input('new-project-name', 'value'),
    prevent_initial_call=True
)
def disable_create_project_bn(value):
    """
    Disable or enable button for creating new project.
    """
    return False if value else True


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
    if value:
        if not hide:
            return selected_project, value

        for d in data:
            if d['name'] == value:
                return d['_id'], ''

    if len(data):
        return data[0]['_id'], ''
    else:
        return '', ''