from dash_extensions.enrich import DashBlueprint, html, Output, Input, State
from dash import dcc
import dash
import plotly.express as px
import pandas as pd
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import callback_context, ctx

from ..utils.helpers import generate_graph_DataTable

### Using dash blueprints as an example, will determine if I want to do that
### or if I use the @dash.callback operator.  Currently not sure what is easier.
# # bp = DashBlueprint()
# # bp.layout = html.Div([html.Button("Click me!", id="btn"), html.Div(id="log")])


# @bp.callback(Output("log", "children"), Input("btn", "n_clicks"))
# def on_click(n_clicks):
#     return f"Hello world {n_clicks}!"


stats_graphs_layout = html.Div(
    html.Div(
        [
            html.Div(
                [
                    dmc.Switch(
                        size="lg",
                        radius="sm",
                        id="graph1-switch",
                        label="Table View",
                        checked=False,
                    ),
                    html.Div([], className="graph_div", id="graph1-div"),
                    dbc.Button(
                        "Full Screen",
                        id="graph1-fullscreen-btn",
                        color="primary",
                        n_clicks=0,
                        style={"width": "15%"},
                    ),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "align-items": "center",
                },
                className="six columns",
            ),
            html.Div(
                [
                    dmc.Switch(
                        size="lg",
                        radius="sm",
                        label="Table View",
                        id="graph2-switch",
                        checked=False,
                    ),
                    html.Div([], className="graph_div", id="graph2-div"),
                    dbc.Button(
                        "Full Screen",
                        id="graph2-fullscreen-btn",
                        color="primary",
                        n_clicks=0,
                        style={"width": "15%"},
                    ),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "align-items": "center",
                },
                className="six columns",
            )
            # html.Div([], className="four columns", id="graph3-div"),
        ],
        style={"padding-top": "30px"},
    ),
    className="twelve columns",
)


### This callback should only update the graphs when data in the main data store changes
## Not sure if I have the proper call back structure to make sure these get populated


@dash.callback(
    [
        Output("graph1-div", "children"),
        Output("graph2-div", "children"),
    ],
    [Input("graph1-switch", "checked"), Input("graph2-switch", "checked"), Input("store", "data")],
    #   [State("store", "data")],
)
def populate_graph_data(graph1_switch, graph2_switch, data):
    print(ctx.triggered, data)
    if data is None:
        return None, None
    else:
        samples_dataset = pd.DataFrame(data)

    if samples_dataset.empty:
        currentStain = None
        currentRegion = None
    else:
        currentStain = (dcc.Graph(figure=px.histogram(samples_dataset, x="stainID")),)
        currentRegion = dcc.Graph(figure=px.histogram(samples_dataset, x="regionName"))
        if graph1_switch:
            currentStain_ds = samples_dataset.groupby("stainID")["_id"].count().reset_index(name="count")
            currentStain = generate_graph_DataTable(currentStain_ds, "graph_dataTable1")
        if graph2_switch:
            currentRegion_ds = samples_dataset.groupby("regionName")["_id"].count().reset_index(name="count")
            currentRegion = generate_graph_DataTable(currentRegion_ds, "graph_dataTable2")

    return [currentStain, currentRegion]


@dash.callback(
    [
        Output("modal-body", "children"),
        Output("modal", "is_open"),
    ],
    [
        Input("graph1-fullscreen-btn", "n_clicks"),
        Input("graph2-fullscreen-btn", "n_clicks"),
        State("graph1-div", "children"),
        State("graph2-div", "children"),
    ],
    prevent_initial_call=True,
)
def make_graph_fullscreen(nclicks1, nclicks2, graph1, graph2):
    trigger = callback_context.triggered[0]
    btn_id = trigger["prop_id"].split(".")[0]
    if btn_id == "graph1-fullscreen-btn":
        return [graph1, True]
    elif btn_id == "graph2-fullscreen-btn":
        return [graph2, True]
