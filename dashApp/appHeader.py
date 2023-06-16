from dash import html
import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.Button("Login", id='login-btn'),
    ],
    brand="NeuroTK Dashboard",
    brand_href="#",
    color="primary",
    dark=True,
)


def getAppHeader():
    return navbar
