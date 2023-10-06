"""
Serves the root application layout.
"""
import dash_bootstrap_components as dbc
from src.components import banner, app_tabs

import dash
from dash import html
from src.utils.settings import SingletonDashApp

neuroTK_dashapp = SingletonDashApp()

app = neuroTK_dashapp.app

# This suppresses callback exceptions when running, might not be the best way to do this though!
app.config["suppress_callback_exceptions"] = True

# Assign the layout to the app.
app.layout = html.Div([banner, app_tabs])


if __name__ == "__main__":
    # To do: debug parameter may want to be set in .env or setting.py instead
    # of hard coded.
    app.run_server(debug=True, threaded=True)
