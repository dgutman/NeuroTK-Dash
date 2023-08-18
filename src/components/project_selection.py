"""
This div should contain the project selection functionality including the
dropdown menu to select available projects to the user, and the ability to
create new projects via button.
"""
from dash import html, dcc, Output, Input, callback
from ..utils import get_projects
from ..settings import gc, PROJECTS_FLD_ID
from dash_mantine_components import Select
import dash_bootstrap_components as dbc


project_selection = html.Div([
    dcc.Store(id='projects-store', data=get_projects(gc, PROJECTS_FLD_ID)),
    dbc.Row([
        dbc.Col(html.Div('Select project: ', style={'fontWeight': 'bold'}), 
                align='start', width='auto'),
        dbc.Col(html.Div(Select(data=[], id='projects-dropdown'))),
        dbc.Col(html.Div(
            html.Button([html.I(className="fa-solid fa-plus" )], 
                        title='create new project')
        ), align='end', width='auto'),
        dbc.Col(html.Div(html.Button(
            [html.I(className="fa-solid fa-trash" )], 
            title='delete selected project', id='delete-project')
            ), align='end', width='auto')
])
], id='project-selection')


@callback(
    [
        Output('projects-dropdown', 'data'), 
        Output('projects-dropdown', 'value'),
        Output('projects-dropdown', 'placeholder'), 
        Output('delete-project', 'disabled')
    ],
    Input('projects-store', 'data')
)
def populate_projects(data):
    """Add values to the project dropdown."""
    options = []

    for project in data:
        options.append({'value': project['key'], 'label': project['key']})

    if len(options):
        return options, options[0]['value'], '', False
    else:
        return [], '', 'No projects found.', True
