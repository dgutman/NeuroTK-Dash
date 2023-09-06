from dash import html
from ..utils.settings import USER

banner = html.Div(
    [
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
                "Log out", id="login-bn", 
                style={'background-color': '#6384c6', 'color': '#fcfcfc'}
            ),
            style={"width": "auto", "display": "inline-block"} 
        ),
    ],
    style={"border": "2px black solid", 'background-color': '#002878'},
    id="banner",
)
