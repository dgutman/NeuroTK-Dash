"""
Selection of task through the a dropdown or creating of a new task via a 
button popup window.
"""
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
from dash_mantine_components import Select
from ..settings import gc

task_selection = html.Div([
    dcc.Store(id='task-store', data=[]),
    dbc.Row([
        dbc.Col(html.Div(
            'Select task: ', style={'fontWeight': 'bold'}
            ), align='start', width='auto'),
        dbc.Col(html.Div(Select(
            data=[], id='tasks-dropdown'))),
        dbc.Col(html.Div(html.Button(
            [html.I(className="fa-solid fa-plus" )], title='create new task'),
            id='create-task'
            ), align='end', width='auto'),
        dbc.Col(html.Div(html.Button(
            [html.I(className="fa-solid fa-trash" )], 
            title='delete selected task', id='delete-task')
            ), align='end', width='auto')
    ])
], id='task-selection')


@callback(
    [
        Output('tasks-dropdown', 'data'), Output('tasks-dropdown', 'value'),
        Output('tasks-dropdown', 'placeholder'),
        Output('delete-task', 'disabled')
    ],
    [Input('projects-dropdown', 'value'), Input('projects-store', 'data')]
)
def populate_tasks(value, data):
    """Populate the task dropdown from the value in projects dropdown."""
    projects = []

    for project in data:
        if project['key'] == value:
            for item in gc.listItem(project['_id']):
                projects.append({'value': item['name'], 'label': item['name']})

    if len(projects):
        return projects, projects[0]['value'], '', False
    else:
        return [], '', 'No tasks in project.', True
