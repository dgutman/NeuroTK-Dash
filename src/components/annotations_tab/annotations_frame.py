from dash import html, Input, Output, State, dcc, callback_context
import dash
from ...utils.settings import gc, dbConn, SingletonDashApp, USER
import plotly.express as px
import plotly.graph_objs as go

import dash_bootstrap_components as dbc
from ...utils.helpers import generate_generic_DataTable
import pandas as pd
from dash_ag_grid import AgGrid
from ...utils.api import getAllItemAnnotations

## Note because of the way I am importing the app object, do NOT use @callback, use app.callback here

curAppObject = SingletonDashApp()
# print(curAppObject.app.title, "Object was loaded..")

app = curAppObject.app  ## I find this very confusing..

from ...utils.database import (
    getAnnotationNameCount,
    getUniqueParamSets,
    getElementSizeForAnnotations,
    insertAnnotationData,
)


## Currently this panel has two related tables..
## One is the annotation counts for any/all annotations in the DSA system
## the other one is unique parameters/other specs that I parse from the
## annotations.. this makes the most sense for positive pixel count
## but may work for others depending on what type of data we are stuffing in them

unique_annots_datatable = html.Div([], id="unique_annots_datatable_div")

## This provides details depending on the type of annotation being displayed..
annotation_details_panel = html.Div(id="annotation_details_panel")

unique_params_datatable = html.Div(
    [AgGrid(id="annotation_name_counts_table")], id="unique_params_datatable_div"
)

## Adding in some temp code to learn how to do async callbacks

button_controls = html.Div(
    [
        html.Button(
            id="cancel_button_id",
            className="mr-2 btn btn-danger",
            children="Cancel Running Job!",
        ),
        html.Button(
            "Refresh anotation data",
            className="mr-2 btn btn-primary",
            id="refresh-annotations-button",
        ),
        html.Button(
            "Pull Full Annotation",
            id="pull-full-annotation-button",
            className="mr-2 btn btn-warning",
        ),
        html.Button(
            "Pull Girder Annotations",
            id="pull-from-girder-button",
            className="mr-2 btn btn-warning",
        ),
    ],
    className="d-grid gap-2 d-md-flex justify-content-md-begin",
)


## TO DO: Refactor style bar so it is on top of the buttons
annotations_frame = html.Div(
    [
        html.Div(id="annotationPull_status"),
        dcc.Store(id="annotations_store"),
        button_controls,
        dbc.Progress(
            id="annotationDetails_update_pbar",
            className="progress-bar-success",
            style={"visibility": "hidden", "width": 250},
        ),
        dbc.Row(
            [
                dbc.Col([unique_annots_datatable], width=5),
                dbc.Col(
                    [dbc.Row([unique_params_datatable])],
                    width=2,
                ),
                dbc.Col(annotation_details_panel, width=5),
            ]
        ),
    ],
)


@app.long_callback(
    output=Output("annotationPull_status", "children"),
    inputs=[
        Input("pull-full-annotation-button", "n_clicks"),
        State("curProjectName_store", "data"),
    ],
    running=[
        (Output("pull-full-annotation-button", "disabled"), True, False),
        (Output("cancel_button_id", "disabled"), False, True),
        (
            Output("annotationPull_status", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("annotationDetails_update_pbar", "style"),
            {"visibility": "visible"},
            {"visibility": "hidden"},
        ),
        (
            Output("annotationDetails_update_pbar", "style"),
            {"visibility": "visible"},
            {"visibility": "visible"},
        ),
    ],
    cancel=[Input("cancel_button_id", "n_clicks")],
    progress=[
        Output("annotationDetails_update_pbar", "value"),
        Output("annotationDetails_update_pbar", "label"),
    ],
    prevent_initial_call=True,
)
def pull_annotation_elements(set_progress, n_clicks, projectName):
    """When I pull annotation in bulk, we do not return individual elelements
    as if can be very slow, so this will grab elements in the background and update"""
    collection = dbConn["annotationData"]

    ## Fix logic here in case there aRE no documents with missing elements..
    # Count documents where the "elements" key does not exist filtered by USER
    ## This may eventually cause errors if multiple users have access to the same annotation

    docCount = collection.count_documents(
        {"userName": USER, "annotation.elements": {"$exists": False}}
    )

    # Since I am still debugging,I don't want to run this on more than 100 docs as a time

    print(f"There are a total of {docCount} annotations to look up")

    for i in range(docCount):
        ## pull and update a single annotation document
        # find a document that has no elements
        doc_with_no_element = collection.find_one(
            {"userName": USER, "annotation.elements": {"$exists": False}}
        )
        ## Now pull the data from the api
        fullAnnotationDoc = gc.get(f"annotation/{doc_with_no_element['_id']}")
        collection.update_one(
            {"_id": doc_with_no_element["_id"]}, {"$set": fullAnnotationDoc}
        )

        jobStatuspercent = ((i + 1) / docCount) * 100
        set_progress((str(i + 1), f"{jobStatuspercent:.2f}%"))
    return dash.no_update
    # return [f"Clicked {n_clicks} times"] ## I actually don't want this div to be updated


debug = False


## TO DO is add long callback here
## This pulls the entire list of accessible annotations from the girder Database
## TO DO:  Add in some sort of date filter by last updated perhaps?
@app.callback(
    Output("annotations_store", "data"),
    Input("pull-from-girder-button", "n_clicks"),
    State("curProjectName_store", "data"),
    # prevent_initial_call=True,
)
def pullBasicAnnotationDataFromGirder(n_clicks, curProjectName):
    if n_clicks:
        print("Available annotations being pulled")
        allAvailableAnnotations = getAllItemAnnotations()
        print(len(allAvailableAnnotations))

        status = insertAnnotationData(allAvailableAnnotations, USER)
        if debug:
            print(status)
    else:
        allAvailableAnnotations = getAnnotationNameCount(USER)
        return allAvailableAnnotations

    ## TO   DO-- MAKE THIS ASYNCHRONOUS


@app.callback(
    Output("unique_annots_datatable_div", "children"),
    Input("refresh-annotations-button", "n_clicks"),
    State("curProjectName_store", "data"),
    # prevent_initial_call=True,
)
def createAnnotationNameCountTable(n_clicks, projectName, debug=False):
    """This gets the list of distinct annotation names and returns a table with the numer and names of annotations"""

    ## Need to make sure we deal with case where there is no annotation
    ## that has ever been pulled from girder.

    annotationCount = pd.DataFrame(getAnnotationNameCount(USER))
    if len(annotationCount) > 0:
        annotationCountPanel = generate_generic_DataTable(
            annotationCount, id_val="annotation_name_counts_table"
        )

        return [annotationCountPanel]


@app.callback(
    Output("annotation_details_panel", "children"),
    Input("annotation_name_counts_table", "cellClicked"),
    State("annotation_name_counts_table", "virtualRowData"),
    prevent_initial_call=True,
)
def generateAnnotationSpecificViz(cellClicked, rowData):
    ## Depending on the annotation cell Clicked, this may generate different graphs
    ## or functionality, for example I may want to look at the # of points in
    ## a gray matter annotation
    if cellClicked:
        row = cellClicked["rowIndex"]
        annot_name = rowData[row]["annotationName"]
        print(annot_name, "in new container was clicked")
        ## Now comes.. graphing..
        points_array = getElementSizeForAnnotations(annot_name)

        # Create the histogram
        fig = go.Figure(data=[go.Histogram(x=points_array)])

        # Optional: Add titles and labels
        fig.update_layout(
            title="Distribution of Points in Annotations",
            xaxis_title="Number of Points",
            yaxis_title="Frequency",
        )

        return dcc.Graph(figure=fig)


@app.callback(
    [Output("unique_params_datatable_div", "children")],
    [
        Input("annotation_name_counts_table", "cellClicked"),
        State("annotation_name_counts_table", "virtualRowData"),
    ],
    prevent_initial_call=True,
)
# NOTE: Given the underlying DB logic which pulls and filters these, only "Positive Pixel Count" really works
# all/most others return only the count, since they don't necessarily have hue, intensity limits, etc.
# and it's currently hardcoded to count/filter based on those values, and only knows to display them as well
def showUniqueParamSets(cellClicked, rowData):
    if cellClicked:
        row = cellClicked["rowIndex"]
        annot_name = rowData[row]["annotationName"]

        paramSets = pd.DataFrame(getUniqueParamSets(annot_name))
        paramSets = generate_generic_DataTable(
            paramSets, id_val="annotation_params_table"
        )

        return [paramSets]

    else:
        return [None]
