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

from src.components import neuroTKnavbar as navbar
from src.components import projectSelector as projSelect

# local imports
from src.utils.settings import (
    APP_HOST,
    APP_PORT,
)


## Was Dash Proxy, removing that functionality for now
app = dash.Dash(
    __name__,
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
    title="NeuroTK Dashboard",
)


accordion_panel = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    html.P("This is the content of the first section"),
                    dbc.Button("Click here"),
                ],
                title="Item 1",
            ),
            dbc.AccordionItem(
                [
                   projSelect.project_panel
                ],
                title="Project Selector",
            ),
            dbc.AccordionItem(
                "This is the content of the third section",
                title="Item 3",
            ),
        ],
    )
)



def serve_layout():
    """Define the layout of the application"""
    return html.Div(
        [
            navbar.navbar_layout,
            accordion_panel
        ],
        className="app__container",
    )


app.layout = serve_layout()


# serve_layout()  # set the layout to the serve_layout function
server = app.server  # the server is needed to deploy the application

if __name__ == "__main__":
    app.run_server(
        host=APP_HOST,
        port=APP_PORT,
        debug=True,
#        dev_tools_props_check=DEV_TOOLS_PROPS_CHECK,
    )
