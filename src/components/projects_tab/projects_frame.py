"""
This file contains the HTML view loaded when the "Projects" tab is selected.

Components include project and task selection (dropdowns), datatable and 
dataview components, and buttons to add and delete new projects and tasks.
"""
from dash import html

from .project_selection import project_selection
from .task_selection import task_selection
from .dataset_view import dataset_view

# Main div variable that is loaded into main application.
projects_frame = html.Div([
    project_selection,
    task_selection,
    dataset_view
], id="projects-frame")
