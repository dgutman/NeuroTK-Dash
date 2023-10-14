"""
Results panel.
"""
from dash import html, callback, Output, Input, no_update
from .report_panels import ppc_report
from .report_panels import nft_report

report = html.Div(
    html.P("Select a task with CLI run to display report."),
    style={"height": "100vh"},
    id="report-tab",
)


@callback(
    Output("report-tab", "children"),
    Input("report-store", "data"),
    suppress_initial_call=True,
)
def load_report_panel(results_store):
    """Load the appropriate report panel - based on the CLI that the currently
    task chosen ran.

    """
    if "cli" in results_store:
        cli = results_store["cli"]
        if cli == "PositivePixelCount":
            return ppc_report
        elif cli == "NFTDetection":
            return nft_report
        else:
            return html.Div(f"Report panel for CLI {cli} is not currently supported.")
    return no_update
