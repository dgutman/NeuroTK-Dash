import dash
from dash import html
from ..settings import USER

banner = html.Div(
    [
        html.Div(html.H4(
                'NeuroTK', className='app__header__title'
            ), style={'width': '49%', 'display': 'inline-block'}
        ),
        html.Div(html.P(children=[
                'Logged in as ', html.Strong(f'{USER}')]
            ), style={'width': '24%', 'display': 'inline-block'}
        ),
        html.Div(html.Button(
                'Log out', id='login-bn', n_clicks=0
            ), style={'width': '24%', 'display': 'inline-block'}
        )
    ],
    style={"border":"2px black solid"},
    id='banner'
)
