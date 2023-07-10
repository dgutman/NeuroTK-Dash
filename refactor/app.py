# notes
"""
This file is for housing the main dash application.
This is where we define the various css items to fetch as well as the layout of our application.
"""

# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc
from flask import Flask
import os

# local imports
from src.utils.settings import (
    APP_HOST,
    APP_PORT,
    DEV_TOOLS_PROPS_CHECK,
    MONGO_URI,
    MONGODB_USERNAME,
    MONGODB_PASSWORD,
    MONGODB_HOST,
    MONGODB_PORT,
    MONGODB_DB,
)
from src.utils.database import db
from src.components import header

from src.utils.settings import MONGO_URI

# create the extension
server = Flask(__name__)
server.config["MONGODB_SETTINGS"] = {
    "host": MONGODB_HOST,
    "username": MONGODB_USERNAME,
    "password": MONGODB_PASSWORD,
    "port": int(MONGODB_PORT),
    "db": MONGODB_DB,
}  # Replace with your MongoDB connection URI
print(server.config["MONGODB_SETTINGS"])
with server.app_context():
    db.init_app(server)


app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,  # turn on Dash pages
    pages_folder=os.path.join(os.path.dirname(__file__), "src", "pages"),
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],  # fetch the proper css items we want
    meta_tags=[
        {  # check if device is a mobile device. This is a must if you do any mobile styling
            "name": "viewport",
            "content": "width=device-width, initial-scale=1",
        }
    ],
    suppress_callback_exceptions=True,
    title="NeuroTK Dashboard",
)


def serve_layout():
    """Define the layout of the application"""
    return html.Div(
        [
            html.Div(
                [
                    header,
                    html.Div(dash.page_container, className="twelve columns"),
                ],
                className="app__content",
            ),
        ],
        className="app__container",
    )


app.layout = serve_layout()  # set the layout to the serve_layout function
server = app.server  # the server is needed to deploy the application

if __name__ == "__main__":
    app.run_server(host=APP_HOST, port=APP_PORT, debug=True, dev_tools_props_check=DEV_TOOLS_PROPS_CHECK)
