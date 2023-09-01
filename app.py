"""
Serves the root application layout.
"""
import dash_bootstrap_components as dbc
from src.components import banner, app_tabs

import dash
from dash import html


def main():
    """Main function."""
    # Application.
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            dbc.icons.FONT_AWESOME,
        ],
        title="NeuroTK",
    )

    # Assign the layout to the app.
    app.layout = html.Div([banner, app_tabs])

    return app


if __name__ == "__main__":
    app = main()

    # To do: debug parameter may want to be set in .env or setting.py instead
    # of hard coded.
    app.run_server(debug=True, threaded=True)
