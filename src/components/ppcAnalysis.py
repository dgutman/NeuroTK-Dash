### This will include various tabs and compoents I am using for PPC analysis
## Will likely migrate some of these subcomponents into a different location as things evolve
import dash
from dash import html, Input, Output, State

from .dsa_cli_view import dsa_cli_view_layout


ppcRunner_frame = html.Div([dsa_cli_view_layout])
