"""This provide some statistics about what annotations are currently loaded in the database and can further dive into params"""
from dash import html, callback, Input, Output, State
from ..utils.database import getAnnotationNameCount, getUniqueParamSets
import dash_bootstrap_components as dbc
from ..utils.helpers import generate_generic_DataTable
import pandas as pd

debug = False
#### First I will create a control / table that lists all of the annotationNames and counts


unique_annots_datatable = html.Div(id="unique_annots_datatable_div")
unique_params_datatable = html.Div(id="unique_params_datatable_div")


annotations_stats_interface_panel = html.Div(
    dbc.Row(
        [
            dbc.Col([unique_annots_datatable], width=5),
            dbc.Col([unique_params_datatable], width=7),
        ]
    )
)


@callback(
    [Output("unique_annots_datatable_div", "children")],
    [Input("unique_annots_accordion", "n_clicks")],
)
def createAnnotationNameCountTable(n_clicks, projectName="evanPPC"):
    """This gets the list of distinct annotation names and returns a table with the numer and names of annotations"""
    annotationCount = pd.DataFrame(getAnnotationNameCount(projectName))

    if debug:
        print(annotationCount)

    annotationCountPanel = generate_generic_DataTable(annotationCount, id_val="annotation_name_counts_table")

    return [annotationCountPanel]


@callback(
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
        paramSets = generate_generic_DataTable(paramSets, id_val="annotation_params_table")

        return [paramSets]

    else:
        return [None]
