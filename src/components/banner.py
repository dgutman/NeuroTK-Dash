import dash
from dash import html

banner = html.Div(
    [
        html.Div(html.H4(
                'NeuroTK Dashboard', className='app__header__title'
            ), style={'width': '49%', 'display': 'inline-block'}
        ),
        html.Div(html.P(
                'Logged in as jvizcar'
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
