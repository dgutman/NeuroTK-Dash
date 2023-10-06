import dash_mantine_components as dmc
import pandas as pd
import re

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
from dash import html, callback, Input, State, Output, dcc

stat_list = [
    "IntensityAverage",
    "IntensityAverageWeakAndPositive",
    "IntensitySumPositive",
    "IntensitySumStrongPositive",
    "IntensitySumWeakPositive",
    "NumberPositive",
    "NumberStrongPositive",
    "NumberTotalPixels",
    "NumberWeakPositive",
    "RatioStrongToPixels",
    "RatioStrongToTotal",
    "RatioTotalToPixels",
    "RatioWeakToPixels",
]


stats = [{"value": stat, "label": stat} for stat in stat_list]

ppc_results_panel = html.Div(
    [
        dmc.Select(
            label="Select PPC result stat to plot:",
            id="selectPPCResultSet",
            data=stats,
            value="RatioStrongToPixels",
            style={"maxWidth": 200},
        ),
        html.Div(id="stat-per-patient-graph", style={"height": "100vh"}),
    ]
)


def make_ppc_box_chart(metadata_df, selected_stat):
    """
    Makes multipanel figure where each panel is a box chart for a particular
    diagnostic/staging framework.

    Generates (modified) version of figure 8 from Dunn aBeta PPC paper.

    """
    metadata_df["npClinical-Braak Stage"] = (
        metadata_df["npClinical-Braak Stage"].str.replace("(", "").str.replace(")", "")
    )

    meta_cols = [
        "npSchema-caseID",
        "npClinical-ABC",
        "npClinical-Braak Stage",
        "npClinical-CERAD",
        "npClinical-Thal",
        selected_stat,
    ]
    metadata_df = metadata_df[meta_cols].copy()

    metadata_df.dropna(subset=meta_cols[1:-1], how="all", inplace=True)

    metadata_df = metadata_df.groupby(meta_cols[:-1], group_keys=False).mean()
    metadata_df.reset_index(inplace=True, drop=False)

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=meta_cols[1:-1],
        shared_yaxes=True,
        y_title=selected_stat,
        x_title="Stage",
        row_heights=[1000, 1000],
    )
    mapping = {
        "npClinical-ABC": (1, 1),
        "npClinical-Braak Stage": (1, 2),
        # "npClinical-CERAD": (2, 1),
        # "npClinical-Thal": (2, 2),
    }

    psp = metadata_df[selected_stat].tolist()

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
        title_text=f"{selected_stat} by Stage of Given Diagnostic Framework",
    )

    return dcc.Graph(figure=fig)


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


def clean_up_df_cols(df):
    # Remove the dataframe columns that are very nested.
    return df.rename(columns=lambda x: re.sub("annotation-attributes-stats-", "", x))


@callback(
    Output("stat-per-patient-graph", "children"),
    Input("selectPPCResultSet", "value"),
    State("results-store", "data"),
    prevent_initial_callback=True,
)
def plot_first_graph(selected_stat, data):
    if selected_stat and data:
        df = pd.json_normalize(data, sep="-")

        df = clean_up_df_cols(df)

        df = df.sort_values(by=["npClinical-Thal", "npSchema-caseID"]).reset_index(
            drop=True
        )

        # stacked_ppc_graph = make_stacked_ppc_bar_chart(df, selected_stat)

        stacked_ppc_graph = make_ppc_box_chart(df, selected_stat)

        return stacked_ppc_graph
    else:
        return dash.no_update
