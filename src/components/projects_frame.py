"""
This file contains the HTML view loaded when the "Projects" tab is selected.

Components include project and task selection (dropdowns), datatable and 
dataview components, and buttons to add and delete new projects and tasks.
"""
from dash import html, Output, Input, callback, dcc
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd

from .project_selection import project_selection
from .task_selection import task_selection
from .dataset_view import dataset_view

# Main div variable that is loaded into main application.
projects_frame = html.Div([
    project_selection,
    task_selection,
    dataset_view
], id="projects-frame")

