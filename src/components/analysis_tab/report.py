"""
Results panel.
"""
from dash import html, callback, Output, Input, State, no_update

report = html.Div(
    html.P("Task results will go here."), style={"height": "100vh"}, id="report-tab"
)


@callback(
    Output('report-tab', 'children'),
    Input('results-store', 'data'),
    suppress_initial_call=True
)
