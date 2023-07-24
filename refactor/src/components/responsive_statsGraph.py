from dash_extensions.enrich import html, Output, Input, State
from dash import dcc, ctx
import dash
import plotly.express as px
import pandas as pd
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import callback_context

from plotly import graph_objects as go

from ..utils.helpers import generate_main_DataTable

### Using dash blueprints as an example, will determine if I want to do that
### or if I use the @dash.callback operator.  Currently not sure what is easier.
# # bp = DashBlueprint()
# # bp.layout = html.Div([html.Button("Click me!", id="btn"), html.Div(id="log")])


# @bp.callback(Output("log", "children"), Input("btn", "n_clicks"))
# def on_click(n_clicks):
#     return f"Hello world {n_clicks}!"


responsive_stats_graphs_layout = html.Div(
    html.Div(
        [
            html.Div(
                [
                    html.Div([], className="graph_div", id="stain_graph_div"),
                    dbc.Button(
                        "Full Screen",
                        id="graph1-fullscreen-btn",
                        color="primary",
                        n_clicks=0,
                        className="fullScreenButton",
                    ),
                    html.Div([], className="table_div", id="stain_table_div", style={"padding-top": "10px"}),
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
                    html.Div([], className="graph_div", id="region_graph_div"),
                    dbc.Button(
                        "Full Screen",
                        id="graph2-fullscreen-btn",
                        color="primary",
                        n_clicks=0,
                        className="fullScreenButton",
                    ),
                    html.Div([], className="table_div", id="region_table_div", style={"padding-top": "10px"}),
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

# TODO: rewrite how this is done such that toggling the switch of one data subset won't reset
# the data of the other. currently filtering one, then toggling the other resets both

# probably make graphs by default and have toggle be independent functions, etc.


@dash.callback(
    [
        Output("stain_graph_div", "children"),
        Output("stain_table_div", "children"),
    ],
    [
        Input("store", "data"),
    ],
)
def populate_stain_div_data(data):
    if data is None:
        return None, None
    else:
        samples_dataset = pd.DataFrame(data)

    if samples_dataset.empty:
        currentStain_graph, currentStain_table = None, None
    else:
        currentStain_graph = dcc.Graph(figure=px.histogram(samples_dataset, x="stainID"), id="stain_graph")

        currentStain_ds = samples_dataset.groupby("stainID")["_id"].count().reset_index(name="count")
        currentStain_table = generate_main_DataTable(currentStain_ds, id_val="stain_data_table")

    return [currentStain_graph, currentStain_table]


@dash.callback(
    [
        Output("stain_data_table", "rowData"),
        Output("stain_data_table", "filterModel"),
        Output("stain_graph", "figure"),
    ],
    [
        Input("stain_data_table", "filterModel"),
        State("store", "data"),
        State("stain_data_table", "virtualRowData"),
    ],
    prevent_initial_call=True,
)
def update_stain_div_data(filterModel, data, virtualRowData):
    if virtualRowData and (data != virtualRowData):
        graph_data = pd.DataFrame.from_dict(virtualRowData)
        figure = go.Figure(px.histogram(graph_data, x="stainID", y="count"))
        return virtualRowData, filterModel, figure

    data = pd.DataFrame.from_dict(data).groupby("stainID")["_id"].count().reset_index(name="count")
    figure = go.Figure(px.histogram(data, x="stainID", y="count"))

    return data.to_dict(orient="records"), {}, figure


@dash.callback(
    [
        Output("region_graph_div", "children"),
        Output("region_table_div", "children"),
    ],
    [
        Input("store", "data"),
    ],
)
def populate_region_div_data(data):
    if data is None:
        return None, None
    else:
        samples_dataset = pd.DataFrame(data)

    if samples_dataset.empty:
        currentRegion_graph, currentRegion_table = None, None

    else:
        currentRegion_graph = dcc.Graph(figure=px.histogram(samples_dataset, x="regionName"), id="region_graph")

        currentRegion_ds = samples_dataset.groupby("regionName")["_id"].count().reset_index(name="count")
        currentRegion_table = generate_main_DataTable(currentRegion_ds, id_val="region_data_table")

    return [currentRegion_graph, currentRegion_table]


@dash.callback(
    [
        Output("region_data_table", "rowData"),
        Output("region_data_table", "filterModel"),
        Output("region_graph", "figure"),
    ],
    [
        Input("region_data_table", "filterModel"),
        State("store", "data"),
        State("region_data_table", "virtualRowData"),
    ],
    prevent_initial_call=True,
)
def update_region_div_data(filterModel, data, virtualRowData):
    if virtualRowData and (data != virtualRowData):
        graph_data = pd.DataFrame.from_dict(virtualRowData)
        figure = go.Figure(px.histogram(graph_data, x="regionName", y="count"))
        return virtualRowData, filterModel, figure

    data = pd.DataFrame.from_dict(data).groupby("regionName")["_id"].count().reset_index(name="count")
    figure = go.Figure(px.histogram(data, x="regionName", y="count"))

    return data.to_dict(orient="records"), {}, figure


# NOTE: below commented out because I didn't want to mess with the buttons since that wasn't really important
# focus was on decoupling the tables/graphs for stain/region so that messing with one doesn't impact the other

# @dash.callback(
#     [
#         Output("modal-body", "children"),
#         Output("modal", "is_open"),
#     ],
#     [
#         Input("graph1-fullscreen-btn", "n_clicks"),
#         Input("graph2-fullscreen-btn", "n_clicks"),
#         State("graph1-div", "children"),
#         State("graph2-div", "children"),
#     ],
#     prevent_initial_call=True,
# )
# def make_graph_fullscreen(nclicks1, nclicks2, graph1, graph2):
#     trigger = callback_context.triggered[0]
#     btn_id = trigger["prop_id"].split(".")[0]
#     if btn_id == "graph1-fullscreen-btn":
#         return [graph1, True]
#     elif btn_id == "graph2-fullscreen-btn":
#         return [graph2, True]
