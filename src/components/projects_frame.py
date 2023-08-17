"""
This is the div / frame where we will put the project dropdown, create new
project button, task dropdown, create new task button, and the dataset 
components.
"""
from dash import html, dcc, Output, Input, callback
from ..utils import get_projects
from ..settings import gc, PROJECTS_FLD_ID
# from . import project_selection
from .project_selection import project_selection
from .task_selection import task_selection
from dash_mantine_components import Select


projects_frame = html.Div([
    project_selection, task_selection
], id='projects-frame')
