"""
Results panel.
"""
from dash import html

report = html.Div(
    html.P("Task results will go here."), style={"height": "100vh"}, id="report-tab"
)
