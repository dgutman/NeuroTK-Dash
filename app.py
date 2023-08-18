# Imports
import dash_bootstrap_components as dbc

import dash
from dash import html

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
