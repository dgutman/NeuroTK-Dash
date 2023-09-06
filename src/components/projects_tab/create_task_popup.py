"""
Component with popup windows to create new task.
"""
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, Output, Input, State, callback

from ...utils.settings import USER, PROJECTS_ROOT_FOLDER_ID, gc

create_task_popup = dbc.Modal(
    [
        dbc.ModalHeader('Create Task'),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(
                    dmc.TextInput(
                        id='new-task-name',
                        label='Task name:',
                        placeholder='Input new task name.'
                    )
                ),
                dbc.Col(
                    html.Button(
                        'Create Task',
                        style={'background': '#7df097'},
                        id='create-task-bn',
                        disabled=True
                    )
                )
            ]),
            dbc.Row([
                dmc.Alert('', color='red', id='create-task-alert',
                          hide=True)
            ])
        ])
    ],
    id='create-task-popup',
    is_open=False,
    fullscreen=False
)


@callback(
    Output('create-task-popup', 'is_open'),
    Input('open-create-task-bn', 'n_clicks'),
    prevent_initial_call=True
)
def open_create_task_popup(n_clicks):
    """
    Open the create task popup window.

    """
    if n_clicks:
        return True


@callback(
    Output('create-task-bn', 'disabled'),
    Input('new-task-name', 'value'),
    prevent_initial_call=True
)
def disable_create_task_bn(value):
    """
    Disable or enable button for creating new tasks.
    
    """
    return False if value else True
