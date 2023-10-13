from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pymongo
from ..utils.settings import (
    USER,
    USER_IS_ADMIN,
    MONGO_URI,
    MONGODB_USERNAME,
    MONGODB_PASSWORD,
)

bn_style = {"background-color": "#6384c6", "color": "#fcfcfc"}

banner = html.Div(
    [
        dcc.Location(pathname="http://localhost:8050/", id="url", refresh=False),
        dcc.Store(
            id="admin-store", data={"user": USER, "admin": USER_IS_ADMIN}
        ),  # will store user information
        dbc.Modal(
            [
                dbc.ModalHeader("Admin Tools"),
                html.Div(
                    html.Button("Wipe MongoDB", id="wipe-mongodb-bn", style=bn_style),
                    style={"width": "auto"},
                ),
            ],
            id="admin-tools",
            is_open=False,
            fullscreen=False,
        ),
        html.Div(
            html.H4("NeuroTK", className="app__header__title"),
            style={"width": "20%", "display": "inline-block", "color": "#fcfcfc"},
        ),
        html.Div(
            html.P(id="curProject_disp"),
            style={"width": "20%", "display": "inline-block"},
        ),
        html.Div(
            html.P(id="curTask_disp"),
            style={"width": "20%", "display": "inline-block"},
        ),
        html.Div(
            html.P(children=["Logged in as ", html.Strong(f"{USER}")]),
            style={"width": "20%", "display": "inline-block", "color": "#fcfcfc"},
        ),
        html.Div(
            html.Button(
                "Log out",
                id="login-bn",
                style=bn_style,
            ),
            style={"width": "auto", "display": "inline-block"},
        ),
        html.Div(
            html.Button(
                "Admin Tools",
                id="admin-bn",
                hidden=True,
                style=bn_style,
            ),
            style={"width": "auto", "display": "inline-block"},
        ),
    ],
    style={"border": "2px black solid", "background-color": "#002878"},
    id="banner",
)


@callback(Output("admin-bn", "hidden"), Input("admin-store", "data"))
def toggle_admin_bn(data):
    """Toggle the visibility of the admin button if the user is an admin or off
    if the user is not an admin.

    """
    if data["admin"]:
        return False
    else:
        return True


@callback(
    Output("admin-tools", "is_open"),
    Input("admin-bn", "n_clicks"),
    suppress_initial_call=True,
)
def popup_admin_tools(n_clicks):
    # Open and close the admin tools popup.
    if n_clicks:
        return True
    else:
        return False


@callback(
    Output("url", "refresh"),
    Input("wipe-mongodb-bn", "n_clicks"),
    suppress_initial_call=True,
)
def wipe_mongodb(n_clicks):
    """Wipe the mongo database entirely using this function. Currently it is
    not doing that because I have made use that part is blocked off.

    """
    if n_clicks:
        mc = pymongo.MongoClient(
            MONGO_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD
        )

        # In the future you can wipe specific collections this way:
        # mc.dsaCache.    collection name   .drop()

        # or wipe the entire database like this:
        # mc.drop_database('dsaCache')

        return True
    else:
        return False
