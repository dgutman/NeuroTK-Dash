"""This will contain various functionality related to viewing consolidated results from a given analysis.. starting with PPC"""
from dash import html, Input, Output, State, dcc, ctx, callback
import dash_ag_grid as dag
from ...utils.settings import dbConn
import dash_bootstrap_components as dbc
from ...utils.helpers import generate_generic_DataTable
import pandas as pd
import json
from pprint import pprint
import plotly.express as px

resultSelectOptions = ["There", "Are", "None"]

results_frame = html.Div(
    [
        dcc.Store(id="ppcResults_store", data=[]),
        dbc.Select(
            id="selectPPCResultSet",
            options=resultSelectOptions,
            value=resultSelectOptions[0],
            style={"maxWidth": 200},
        ),
        html.Div(id="ppcResults_graphs_container"),
        html.Div(id="ppcResults_datatable"),
    ]
)


# generates (modified) version of figure 4 from Dunn aBeta PPC paper
def make_stacked_ppc_bar_chart(metadata_df):
    """
    Makes multipanel figure where each panel is a bar chart for a particular stain
    Each bar chart is itself representative of Percent Strong Positive for each region of a particular case
    Which is given as a single bar for each case, subdivided into, and color coded by, region (recreating Dunn fig 4)
    """

    fig = px.bar(
        metadata_df,
        x="npSchema-caseID",
        y="annotation-attributes-stats-RatioStrongToPixels",
        color="npSchema-region",
        facet_col="npSchema-stainID",
        category_orders={
            "npSchema-stainID": sorted(metadata_df["npSchema-stainID"].unique())
        },
        title=f"Percent Strong Positive by Region and Case",
        labels={
            "npSchema-caseID": "Case ID",
            "npSchema-region": "Region",
            "npSchema-stainID": "Stain",
        },
    )
    # NOTE: below update_xaxes can be ommited if desired. only included to force plotly to show all x axis labels
    # if not included, all x axis labels are still there, but some are left out for readability, though will be
    # loaded if a user zooms in to a particular part of the graph or hovers over a given bar
    fig.update_xaxes(tickmode="linear")
    fig.update_layout(xaxis_tickangle=-90)

    return dcc.Graph(figure=fig)


import dash


@callback(
    Output("ppcResults_store", "data"),
    Input("selectPPCResultSet", "value"),
    Input("filteredItem_store", "data"),
)
def populatePPCResultStore(selectValue, taskItem_data):
    """The select value is just a place holder... currently it doesn't do anything but eventually we will want
    to pull results based on the specific selected task and data set... again.. PLACE HOLDER!!
    """
    if taskItem_data:
        # print(len(taskItem_data))
        imageIdList = [x["_id"] for x in taskItem_data]
        imageIdLookupDict = {x["_id"]: x for x in taskItem_data}

    else:
        print("Nothing is in task item store??")
        return dash.no_update, dash.no_update
    # imageIdList = [x["_id"] for x in taskItem_data]
    # print(imageIdList)

    # Get all available annotation documents with positive pixel results.
    if imageIdList:
        ppcDocs = dbConn["annotationData"].find(
            {"annotation.name": "Positive Pixel Count", "itemId": {"$in": imageIdList}},
            {
                "annotation.description": 1,
                "itemId": 1,
                "annotation.attributes.stats": 1,
            },
        )

        # Annotation results are not properly jsonified, so fix this.
        fixedPPC = []

        for p in ppcDocs:
            # resultsWithMetadata = parse_PPC(p)
            # resultsWithMetadata.update(imageIdLookupDict[p["_id"]])
            itemId = p["itemId"]
            if itemId in imageIdLookupDict:
                p.update(imageIdLookupDict[itemId])

            fixedPPC.append(p)

        return fixedPPC


def clean_groups(groups):
    return {
        f"group_{count}": val for count, val in enumerate(groups, 1) if val is not None
    }


# stain

# record["test"] = description

# if record["groups"] is not None:
#     record.update(clean_groups(record["groups"]))

# record.pop("groups")

# return record


@callback(Output("ppcResults_datatable", "children"), Input("ppcResults_store", "data"))
def generatePPCResultsTable(data):
    df = pd.json_normalize(data, sep="-")

    ppcResults_datatable = generate_generic_DataTable(df, "ppc_dt")
    # print(ppcResults_datatable)
    return ppcResults_datatable


@callback(
    Output("ppcResults_graphs_container", "children"), Input("ppcResults_store", "data")
)
def generatePPCRGraphs(data):
    df = pd.json_normalize(data, sep="-")
    stacked_ppc_graph = make_stacked_ppc_bar_chart(df)

    # print(ppcResults_datatable)
    return stacked_ppc_graph


# ppcResults_datatable

## Now return a datatable..


## First create a store to hold the current PPC results...
