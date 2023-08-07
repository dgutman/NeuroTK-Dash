# package imports
import dash
from dash import html, dcc, callback, Output, Input, State, ctx
import dash_bootstrap_components as dbc  # Useful set of layout widgets
import pandas as pd
import dash_mantine_components as dmc
import dash_leaflet as dl

from datetime import date


from ..utils.helpers import getSampleDataset, generate_main_DataTable, generate_generic_DataTable
from ..utils.api import getItemSetData, get_ppc_details_simple
from ..utils.database import insert_records, get_all_records_df
from ..components.statsGraph import stats_graphs_layout
from ..components.responsive_statsGraph import responsive_stats_graphs_layout
from ..components.imageSetViewer import imageSetViewer_layout
from ..components.annotationViewPanel import plotImageAnnotations
from ..components.ppc_results_panel import ppc_results_interface_panel

# NOTE: start mongo db with: sudo serivice mongodb start


dash.register_page(__name__, path="/", redirect_from=["/home"], title="Home")


cur_image_annotationTable = html.Div(id="curImageAnnotation-div")

cur_image_viz = dbc.Col(
    [
        html.Div(
            id="leaflet-map",
            className="twelve columns leaflet-map",
            children=[dl.Map(dl.TileLayer(), style={"width": "1000px", "height": "500px", "marginTop": "25px"})],
        )
    ],
    className="cur-image-viz-tab",
)

main_item_datatable = html.Div([], className="twelve columns item_datatable", id="datatable-div")
simple_ppc_results_datatable = html.Div(
    [],
    className="twelve columns item_datatable",
    id="simple-ppc-results-datatable-div",
)


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
                dmc.AccordionControl("Simple PPC Results Datatable"),
                dmc.AccordionPanel(simple_ppc_results_datatable),
            ],
            id="simple_annots_accordion",
            value="focus_1",
        ),
        dmc.AccordionItem(
            [
                dmc.AccordionControl("Specific PPC Results Datatable"),
                dmc.AccordionPanel(ppc_results_interface_panel),
            ],
            value="focus_2",
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
        dmc.AccordionItem(
            [
                dmc.AccordionControl("Responsive Stats Graphs"),
                dmc.AccordionPanel(responsive_stats_graphs_layout),
            ],
            value="flexibility_1",
        ),
    ]
)


layout = dmc.MantineProvider(
    dmc.NotificationsProvider(
        [
            html.Div([], id="relatedImageSet_layout"),
            html.Div([], id="curImage_annotations"),
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


@callback(
    [
        Output("dag-main-table", "rowData"),
        Output("dag-main-table", "filterModel"),
    ],
    [
        Input("dag-main-table", "filterModel"),
        State("dag-main-table", "virtualRowData"),
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


# This callback should only populate the datatable
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
        table = generate_main_DataTable(samples_dataset, id_val="dag-main-table")

    return [table]


@callback(
    [Output("simple-ppc-results-datatable-div", "children")],
    [Input("simple_annots_accordion", "n_clicks")],
)
def populate_simple_annotations_datatable(n_clicks):
    samples_dataset = get_ppc_details_simple()

    if samples_dataset.empty:
        table = None
    else:
        col_def_dict = {
            "Created On": {
                "field": "Created On",
                "filter": "agDateColumnFilter",
                "filterParams": {"debounceMs": 2500},
                # "flex": 1,
                "editable": True,
                "valueGetter": {"function": "d3.timeParse('%Y-%m-%d')(params.data['Created On])"},
            }
        }

        col_defs = [
            ({"field": col} if col not in col_def_dict else col_def_dict[col]) for col in samples_dataset.columns
        ]
        table = generate_generic_DataTable(samples_dataset, id_val="simple-dag-annotation-table", col_defs=col_defs)

    return [table]


## Creating callback function for when a user clicks on an image
@callback(
    [
        Output("relatedImageSet_layout", "children"),
        Output("curImage_annotations", "children"),
    ],
    [
        Input("dag-main-table", "cellClicked"),
        State("dag-main-table", "rowData"),
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

        # NOTE: this will be done a lot so might be worth figuring out approach which caches df or something
        df = pd.DataFrame().from_dict(data)
        df = df[(df.blockID == blockId) & (df.caseID == caseId) & (df.stainID != stainId)]

        out_vals = (
            [imageSetViewer_layout(df.to_dict(orient="records"))],
            [html.H3(f"{caseId}: {regionName.title()}, Stained with {stainId}"), plotImageAnnotations(imgId)],
        )

        return out_vals

    return [html.Div("")], html.Div()


@callback(
    [
        Output("store", "data"),
        Output("loading", "children"),
    ],
    [Input("update-btn", "n_clicks")],
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
