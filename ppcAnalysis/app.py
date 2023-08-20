# notes
"""
This file is for housing the main dash application.
This is where we define the various css items to fetch as well as the layout of our application.
"""
# package imports
import dash, os
from dash import html
import dash_bootstrap_components as dbc
from flask import Flask

from src.utils.settings import DEV_TOOLS_PROPS_CHECK, APP_HOST, APP_PORT, MONGODB_SETTINGS

from src.components.main_layout import app_layout
from src.utils.database import db

# from src.components.statsGraph import bp as stats_bp, stats_graphs_layout
# local imports
# create the extension
server = Flask(__name__)

server.config["MONGODB_SETTINGS"] = MONGODB_SETTINGS
# print(server.config["MONGODB_SETTINGS"])
with server.app_context():
    db.init_app(server)


## Was Dash Proxy, removing that functionality for now
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
    ],  # fetch the proper css items we want
    meta_tags=[
        {  # check if device is a mobile device. This is a must if you do any mobile styling
            "name": "viewport",
            "content": "width=device-width, initial-scale=1",
        }
    ],
    suppress_callback_exceptions=True,
    title="NeuroTK PPC Dashboard",
)

def serve_layout():
    """Define the layout of the application"""
    return html.Div(
        [
            html.Div(
                [
                    # header,

                    html.Div(app_layout, className="twelve columns"),
                ],
                className="app__content",
            ),
        ],
        className="app__container",
    )

app.layout = serve_layout()  # set the layout to the serve_layout function
server = app.server  # the server is needed to deploy the application

if __name__ == "__main__":
    app.run_server(
        host=APP_HOST,
        port=APP_PORT,
        debug=True,
        dev_tools_props_check=DEV_TOOLS_PROPS_CHECK,
    )
