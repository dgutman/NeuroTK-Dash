### This module creates a layout to view the annotation data from the DSA that is cached locally in a mongo table
## We can add all the filters and fun stuff here related to showing annotations, as well as overlaying annotations on images
### For now we will simply display a datatable... but cooler stuff.. coming soon!
### This module creates a layout to view the annotation data from the DSA that is cached locally in a mongo table
## We can add all the filters and fun stuff here related to showing annotations, as well as overlaying annotations on images
### For now we will simply display a datatable... but cooler stuff.. coming soon!

# from ..utils.api import getAllItemAnnotations
from ..utils.helpers import generate_generic_DataTable
import json
import dash_mantine_components as dmc


"""This provide some statistics about what annotations are currently loaded in the database and can further dive into params"""
from dash import html, callback, Input, Output, State
from ..utils.database import getAnnotationNameCount, getUniqueParamSets
import dash_bootstrap_components as dbc
import pandas as pd
from ..utils.api import getAllItemAnnotations

projectName = "evanPPC"
debug = False


#### First I will create a control / table that lists all of the annotationNames and counts
unique_annots_datatable = html.Div([], id="unique_annots_datatable_div")
unique_params_datatable = html.Div([], id="unique_params_datatable_div")


annotation_analysis_layout = html.Div(
    [
        dbc.Row(
            [
                html.Div("Cache annotations or something?"),
                dbc.Button("Refresh Annotation Data", id="refresh-annotations-button"),
            ]
        ),
        dbc.Row(
            [
                dbc.Col([unique_annots_datatable], width=5),
                dbc.Col([unique_params_datatable], width=7),
            ]
        ),
    ]
)


@callback(
    [Output("unique_annots_datatable_div", "children")],
    [Input("refresh-annotations-button", "n_clicks")],
)
def createAnnotationNameCountTable(n_clicks, projectName="evanPPC"):
    """This gets the list of distinct annotation names and returns a table with the numer and names of annotations"""
    annotationCount = pd.DataFrame(getAnnotationNameCount(projectName))

    if debug:
        print(annotationCount)

    annotationCountPanel = generate_generic_DataTable(
        annotationCount, id_val="annotation_name_counts_table"
    )

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
        paramSets = generate_generic_DataTable(
            paramSets, id_val="annotation_params_table"
        )

        return [paramSets]

    else:
        return [None]


# @callback(
#     [Output("all-annotations-datatable-div", "children")],
#     [Input("all_annots_accordion", "n_clicks")],
# )
# def updateAnnotationDataFromGirder(n_clicks):
#     ### Pull the annotation Data from girder and load it into the mongo database, we will then return a table as well...

#     annotationItemData = getAnnotationData_fromDB(projectName=projectName)

#     if annotationItemData:
#         df = pd.json_normalize(annotationItemData, sep="_")

#         keep_cols = [
#             "_id",
#             "itemId",
#             "created",
#             "projectName",
#             "annotation_name",
#             "annotation_description",
#             "annotation_attributes_stats_RatioStrongToPixels",
#         ]

#         keep_cols.extend([col for col in df.columns if col.startswith("group")])
#         df = df[keep_cols]

#         mapped_vals = {
#             "itemId": "item ID",
#             "_id": "annotation ID",
#             "annotation_name": "Annotation Name",
#             "annotation_description": "Annotation Description",
#             "annotation_attributes_stats_RatioStrongToPixels": "Percent Strong Positive",
#         }
#         df.rename(columns=mapped_vals, inplace=True)

#         df.dropna(how="all", inplace=True)
#         df.dropna(axis=1, how="all", inplace=True)

#         return [generate_generic_DataTable(df, id_val="dag_all_annotations_table")]

#     return [None]

#### First I will create a control / table that lists all of the annotationNames and counts


# unique_annots_datatable = html.Div([], id="unique_annots_datatable_div")
# unique_params_datatable = html.Div([], id="unique_params_datatable_div")


# annotations_stats_interface_panel = html.Div(
#     dbc.Row(
#         [
#             dbc.Col([unique_annots_datatable], width=5),
#             dbc.Col([unique_params_datatable], width=7),
#         ]
#     )
# )


# @callback(
#     [Output("unique_annots_datatable_div", "children")],
#     [Input("annotation_and_param_count_accordion", "n_clicks")],
# )
# def createAnnotationNameCountTable(n_clicks, projectName="evanPPC"):
#     """This gets the list of distinct annotation names and returns a table with the numer and names of annotations"""
#     annotationCount = pd.DataFrame(getAnnotationNameCount(projectName))

#     if debug:
#         print(annotationCount)

#     annotationCountPanel = generate_generic_DataTable(
#         annotationCount, id_val="annotation_name_counts_table"
#     )

#     return [annotationCountPanel]


# @callback(
#     [Output("unique_params_datatable_div", "children")],
#     [
#         Input("annotation_name_counts_table", "cellClicked"),
#         State("annotation_name_counts_table", "virtualRowData"),
#     ],
#     prevent_initial_call=True,
# )
# # NOTE: Given the underlying DB logic which pulls and filters these, only "Positive Pixel Count" really works
# # all/most others return only the count, since they don't necessarily have hue, intensity limits, etc.
# # and it's currently hardcoded to count/filter based on those values, and only knows to display them as well
# def showUniqueParamSets(cellClicked, rowData):
#     if cellClicked:
#         row = cellClicked["rowIndex"]
#         annot_name = rowData[row]["annotationName"]

#         paramSets = pd.DataFrame(getUniqueParamSets(annot_name))
#         paramSets = generate_generic_DataTable(
#             paramSets, id_val="annotation_params_table"
#         )

#         return [paramSets]

#     else:
#         return [None]
