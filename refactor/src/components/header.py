from dash import html
import dash
from ..utils.images import logo_encoded


header = html.Div(
    [
        html.Div(
            [
                html.H4("NeuroTK Dashboard", className="app__header__title"),
            ],
            className="app__header__desc",
        ),
        html.Div(
            [
                html.A(
                    html.Img(
                        src=logo_encoded,
                        className="app__menu__img",
                    ),
                    href="https://plotly.com/dash/",
                ),
            ],
            className="app__header__logo",
        ),
    ],
    className="app__header",
)
