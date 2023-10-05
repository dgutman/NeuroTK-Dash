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

## PPC ParamSet...


# generates (modified) version of figure 8 from Dunn aBeta PPC paper
def make_ppc_box_chart(metadata_df):
    """
    Makes multipanel figure where each panel is a box chart for a particular diagnostic/staging framework
    """

    metadata_df["Braak Stage"] = (
        metadata_df["Braak Stage"].str.replace("(", "").str.replace(")", "")
    )

    meta_cols = [
        "caseID",
        "ABC",
        "Braak Stage",
        "CERAD",
        "Thal",
        "Percent Strong Positive",
    ]
    metadata_df = metadata_df[meta_cols].copy()

    metadata_df.dropna(subset=meta_cols[1:-1], how="all", inplace=True)

    metadata_df = metadata_df.groupby(meta_cols[:-1], group_keys=False).mean()
    metadata_df.reset_index(inplace=True, drop=False)

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=meta_cols[1:-1],
        shared_yaxes=True,
        y_title="Percent Strong Positive",
        x_title="Stage",
    )
    mapping = {"ABC": (1, 1), "Braak Stage": (1, 2), "CERAD": (2, 1), "Thal": (2, 2)}

    psp = metadata_df["Percent Strong Positive"].tolist()

    for col, loc in mapping.items():
        fig.add_trace(
            go.Box(x=metadata_df[col].tolist(), y=psp), row=loc[0], col=loc[1]
        )
        fig.update_xaxes(
            categoryorder="array",
            categoryarray=sorted(metadata_df[col].unique()),
            row=loc[0],
            col=loc[1],
        )

    fig.update_layout(
        showlegend=False,
        title_text="Percent Strong Positive by Stage of Given Diagnostic Framework",
    )

    return dcc.Graph(figure=fig)


analysisProps = [
    "annotation-attributes-stats-IntensityAverage",
    "annotation-attributes-stats-IntensityAverageWeakAndPositive",
    "annotation-attributes-stats-IntensitySumPositive",
    "annotation-attributes-stats-IntensitySumStrongPositive",
    "annotation-attributes-stats-IntensitySumWeakPositive",
    "annotation-attributes-stats-NumberPositive",
    "annotation-attributes-stats-NumberStrongPositive",
    "annotation-attributes-stats-NumberTotalPixels",
    "annotation-attributes-stats-NumberWeakPositive",
    "annotation-attributes-stats-RatioStrongToPixels",
    "annotation-attributes-stats-RatioStrongToTotal",
    "annotation-attributes-stats-RatioTotalToPixels",
    "annotation-attributes-stats-RatioWeakToPixels",
]

ppcResultOptions = []
for ap in analysisProps:
    ppcResultOptions.append({"value": ap, "label": ap.split("-")[-1]})


results_frame = html.Div(
    [
        dcc.Store(id="ppcResults_store", data=[]),
        dbc.Select(
            id="selectPPCResultSet",
            options=ppcResultOptions,
            value=ppcResultOptions[0]["value"],
            style={"maxWidth": 200},
        ),
        html.Div(id="ppcResults_graphs_container"),
        html.Div(id="ppcResults_datatable"),
    ]
)


# generates (modified) version of figure 4 from Dunn aBeta PPC paper
def make_stacked_ppc_bar_chart(metadata_df, propToGraph):
    """
    Makes multipanel figure where each panel is a bar chart for a particular stain
    Each bar chart is itself representative of Percent Strong Positive for each region of a particular case
    Which is given as a single bar for each case, subdivided into, and color coded by, region (recreating Dunn fig 4)
    """
    fig = px.bar(
        metadata_df,
        x="npSchema-caseID",
        y=propToGraph,
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
    Output("ppcResults_graphs_container", "children"),
    Input("ppcResults_store", "data"),
    Input("selectPPCResultSet", "value"),
)
def generatePPCRGraphs(data, propToGraph):
    df = pd.json_normalize(data, sep="-")
    print(propToGraph)
    if data:
        stacked_ppc_graph = make_stacked_ppc_bar_chart(df, propToGraph)

        # print(ppcResults_datatable)
        return stacked_ppc_graph


# ppcResults_datatable

## Now return a datatable..


## First create a store to hold the current PPC results...
