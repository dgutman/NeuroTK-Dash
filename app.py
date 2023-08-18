# Imports
from os.path import join, dirname
import dash_bootstrap_components as dbc
from girder_client import GirderClient
from typing import List

import dash
from dash import html, dcc, Output, Input, callback

import src.settings as settings
from src.components import banner, projects_tabs


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
    ],
    title="NeuroTK Dashboard",
)


def serve_layout():
    """Define the layout of the application."""
    return html.Div([banner, projects_tabs])


# Assign the layout to the app.
app.layout = serve_layout()

if __name__ == "__main__":
    app.run_server(debug=True, threaded=True)
