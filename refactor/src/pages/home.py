# package imports
import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc  # Useful set of layout widgets
import plotly.express as px
import pandas as pd
import dash_mantine_components as dmc
from dash import callback_context
import dash_leaflet as dl


from ..utils.helpers import (
    generate_dsaDataTable,
    getSampleDataset,
    generate_dsaAnnotationsTable,
    generate_graph_DataTable,
)
from ..utils.api import getItemSetData, pull_thumbnail_array, getItemAnnotations
from ..utils.database import insert_records, get_all_records_df
from dash_iconify import DashIconify
from ..components.statsGraph import stats_graphs_layout
from ..components.imageSetViewer import imageSetViewer_layout
from ..components.annotationViewPanel import plotImageAnnotations

# from ..utils.dsa_login import LoginSystem

dash.register_page(__name__, path="/", redirect_from=["/home"], title="Home")


## For development I am checking to see if I am in a docker environment or not..

# dsa_login = LoginSystem("SOME_URL_GOES_HERE") # TO BE DONE

### This contains high level stats graphs for stain and regionName


cur_image_annotationTable = html.Div(id="curImageAnnotation-div")

cur_image_viz = dbc.Col(
    [
        # html.Div(id="cur-image-for-ppc", className="cur-image-for-ppc three columns"),
        # html.Div(cur_image_annotationTable, className="seven columns"),
        # html.Div(id="cur-image-with-annotation", className="two columns"),
        html.Div(
            id="leaflet-map",
            className="twelve columns leaflet-map",
            children=[dl.Map(dl.TileLayer(), style={"width": "1000px", "height": "500px", "marginTop": "25px"})],
        )
    ],
    className="cur-image-viz-tab",
)

main_item_datatable = html.Div([], className="twelve columns item_datatable", id="datatable-div")


multi_acc = dmc.AccordionMultiple(
    children=[
        dmc.AccordionItem(
            [
                dmc.AccordionControl("Item Set Datatable"),
                dmc.AccordionPanel(main_item_datatable),
            ],
            value="focus",
        ),
        dmc.AccordionItem(
            [
                dmc.AccordionControl("Cur Image Viz"),
                dmc.AccordionPanel(cur_image_viz),
            ],
            value="customization",
        ),
        dmc.AccordionItem(
            [
                dmc.AccordionControl("Stats Graphs"),
                dmc.AccordionPanel(stats_graphs_layout),
            ],
            value="flexibility",
        ),
    ]
)


layout = dmc.MantineProvider(
    dmc.NotificationsProvider(
        [
            html.Div("Place Holder for Image Set", id="relatedImageSet_layout"),
            html.Div("Annotation stuff here", id="curImage_annotations"),
            html.Div(
                [
                    dbc.Modal(
                        [
                            dbc.ModalHeader("Full Screen"),
                            dbc.ModalBody(
                                [html.Div([], id="modal-body")],
                            ),
                        ],
                        id="modal",
                        is_open=False,
                        fullscreen=True,
                    ),
                    html.Div(
                        [
                            multi_acc,
                            html.Div(
                                [
                                    dcc.Loading(
                                        id="loading",
                                        type="default",
                                        children=[
                                            html.Button(
                                                "Update Item Data",
                                                id="update-btn",
                                                n_clicks=0,
                                            ),
                                        ],
                                    ),
                                ],
                                className="twelve columns process-btn-div",
                            ),
                        ],
                        className="content__card",
                    ),
                    dcc.Store(id="store", storage_type="memory"),
                    html.Div(id="notification-container"),
                ]
            ),
        ]
    )
)


### What's the best way to make this also update the graphs... do I have to explicitly also include
### The function that updates the graphs here?  or is there some other better way to do it..
## I'd rather the call back function just live in the statsGraph.py file..
@callback(
    [
        Output("dag-annotation-table", "rowData"),
        Output("dag-annotation-table", "filterModel"),
    ],
    [
        Input("dag-annotation-table", "filterModel"),
        State("dag-annotation-table", "virtualRowData"),
        State("store", "data"),
    ],
    prevent_initial_call=True,
)
def update_on_filter(filterModel, virtualRowData, data):
    """
    If the filtered data is not empty and does differ from original data, update the table and keep the filter
    Otherwise, revert to the original data and set the filter to blank so all values are populated in filter again
    """

    if virtualRowData and (data != virtualRowData):
        return virtualRowData, filterModel
    return data, {}


# ### This callback should only populate the datatable
@callback(
    [Output("datatable-div", "children")],
    [Input("store", "data")],
)
def populate_main_datatable(data):
    if data is None:
        samples_dataset = get_all_records_df()
    else:
        samples_dataset = pd.DataFrame(data)

    if samples_dataset.empty:
        table = None
    else:
        # table = generate_dsaDataTable(samples_dataset)
        table = generate_graph_DataTable(samples_dataset)

    return [table]


## CReating callback function for when a user clicks on an image....This is.. confusing!
@callback(
    [
        Output("relatedImageSet_layout", "children"),
        Output("curImage_annotations", "children"),
    ],
    [
        Input("dag-annotation-table", "cellClicked"),
        State("dag-annotation-table", "rowData"),
        State("store", "data"),
    ],
    # (A) pass table as data input to get current value from active cell "coordinates"
    prevent_initial_call=True,
)
def updateRelatedImageSet(cellClicked, rowData, data):
    """
    Here rowData refers to the data from all rows, not selected row
    virtualRowData refers to the data from rows remaining after filter has been applied
    cellClicked is the index of the rowData list where the relevant data lives
    """

    if cellClicked:
        row = cellClicked["rowIndex"]
        col = cellClicked["colId"]

        imgId = rowData[row]["_id"]
        imgName = rowData[row]["name"]
        blockId = rowData[row]["blockID"]
        stainId = rowData[row]["stainID"]
        regionName = rowData[row]["regionName"]
        caseId = rowData[row]["caseID"]

        print(imgName, row, col, imgId)
        ## Now I need to actually.. get all the related images.. this is probably easiest in pandas..
        ## We need to find all the images with the same case_id, and block_id and return the list of items with the other stains

        # NOTE: this will be done a lot so might be worth figuring out approach which caches df or something
        df = pd.DataFrame().from_dict(data)
        ### TO REDO to validate that blockID, caseID, etc actually exist.. and also cleanup

        df = df[(df.blockID == blockId) & (df.caseID == caseId) & (df.stainID != stainId)]

        out_vals = (
            [imageSetViewer_layout(df.to_dict(orient="records"))],
            [html.H3(f"{caseId}: {regionName.title()}, Stained with {stainId}"), plotImageAnnotations(imgId)],
        )

        return out_vals

    return [html.Div("")], html.Div()


@callback(
    Output("store", "data"),
    Output("loading", "children"),
    [Input("update-btn", "n_clicks")],
    ## prevent_initial_call=True,
)
def update_data(n_clicks):
    # n_clicks by default 0 (never observed None), so can do below as if not n_clicks
    if n_clicks is None or n_clicks == 0:  ## Need this to initially load data set
        samples_dataset_records = get_all_records_df().to_dict(orient="records")
        return samples_dataset_records, html.Button("Update", id="update-btn", n_clicks=0)
    else:
        item_set = getItemSetData()
        samples_dataset = getSampleDataset(item_set)
        samples_dataset_records = samples_dataset.to_dict(orient="records")
        insert_records(samples_dataset_records)
        return samples_dataset_records, html.Button("Update", id="update-btn", n_clicks=0)
