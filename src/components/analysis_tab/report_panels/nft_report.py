from dash import html, callback, Input, Output, State, dcc
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from pandas import json_normalize, DataFrame
import plotly.express as px
import pickle
from sklearn.metrics import cohen_kappa_score, confusion_matrix


# def plot_cm(cm: np.array, labels: List[str], title: str = '',
#             figsize: Tuple[int, int] = (4, 4)):
#     """Plot confusion matrix.

#     Args:
#         cm: Confusion matrix with rows are true and columns are predictions.
#         labels: Labels of the confusion matrix.
#         title: Title of plot.
#         figsize: Size of figure.

#     """
#     cm = DataFrame(cm, index=labels, columns=labels)

#     plt.figure(figsize=figsize)
#     ax = sns.heatmap(
#         cm, cmap='viridis', annot=True, cbar=False, fmt=".0f", square=True,
#         linewidths=1, linecolor='black', annot_kws={"size": 18}
#     )
#     ax.xaxis.set_ticks_position("none")
#     ax.yaxis.set_ticks_position("none")
#     ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=14)

#     plt.ylabel('True', fontsize=18, fontweight='bold')
#     ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=14)

#     plt.xlabel('Predicted', fontsize=18, fontweight='bold')
#     plt.title(title, fontsize=14, fontweight='bold')

#     return ax


stages = ["0", "I", "II", "III", "IV", "V", "VI"]

selected_features = [
    "Pre-NFT density (Hippocampus)",
    "iNFT density (Hippocampus)",
    "iNFT FOV count (Hippocampus)",
    "Pre-NFT clustering Coef (r=400) (Hippocampus)",
    "iNFT clustering Coef (r=200) (Hippocampus)",
    "iNFT clustering Coef (r=300) (Hippocampus)",
    "iNFT density (Amygdala)",
    "iNFT FOV count (Amygdala)",
    "iNFT clustering Coef (r=200) (Amygdala)",
    "Pre-NFT density (Temporal cortex)",
    "iNFT density (Temporal cortex)",
    "Pre-NFT FOV count (Temporal cortex)",
    "iNFT FOV count (Temporal cortex)",
    "iNFT clustering Coef (r=150) (Temporal cortex)",
    "iNFT clustering Coef (r=200) (Temporal cortex)",
    "iNFT clustering Coef (r=250) (Temporal cortex)",
    "iNFT clustering Coef (r=300) (Temporal cortex)",
    "Pre-NFT density (Occipital cortex)",
    "iNFT density (Occipital cortex)",
    "iNFT FOV count (Occipital cortex)",
]

nft_report = html.Div(
    [
        dmc.Select(
            label="Select figure or table to plot:",
            id="report-dropdown",
            data=[
                {
                    "value": "summary-table",
                    "label": "Summary stats and demographics table",
                },
                {
                    "value": "counts",
                    "label": "Pre-NFT & iNFT Counts Histogram",
                },
                {"value": "stage-boxplot", "label": "Braak NFT Stage Group Boxplots"},
                {"value": "braak-cm", "label": "Braak NFT Stage Confusion Matrix"},
            ],
            value="summary-table",
            style={"width": "auto"},
        ),
        html.Div(id="report-div"),
    ]
)


def counts_histogram_layout(data):
    """Create the layout of the counts histogram."""
    df = json_normalize(data, sep="-")

    stats = []
    for c in df.columns:
        if c.startswith("annotation-attributes-stats-iNFT"):
            stat = c.split("-attributes-stats-iNFT")[-1]

            stats.append({"label": stat, "value": stat})

    if "npSchema-region" in df:
        regions = [
            {"value": reg, "label": reg} for reg in df["npSchema-region"].unique()
        ]
    else:
        return html.Div("npSchema-region not in data.")

    if len(regions) and len(stats):
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dmc.Select(
                                label="Select region:",
                                id="counts-histogram-region",
                                data=regions,
                                value=regions[0]["value"],
                                style={"width": "auto"},
                            )
                        ),
                        dbc.Col(
                            dmc.Select(
                                label="Select stat:",
                                id="counts-histogram-stat",
                                data=stats,
                                value=stats[0]["value"],
                                style={"width": "auto"},
                            )
                        ),
                    ]
                ),
                html.Div(id="counts-histogram"),
            ]
        )
    else:
        return html.Div("No regions or stats in data.")


def get_confusion_matrix(data):
    """Predict the Braak NFT stages from imaging features."""
    # Reload the model - this is mostly for testing!
    with open("rfc.pkl", "rb") as fh:
        rfc = pickle.load(fh)

    # Format the data in a array to use for predictions.
    df = json_normalize(data, sep="-")
    df = df[df["npClinical-Braak Stage"].isin(stages)]

    stats = []
    for c in df.columns:
        if c.startswith("annotation-attributes-stats-"):
            stats.append(c)

    test_data = []

    regions = ["Amygdala", "Hippocampus", "Occipital cortex", "Temporal cortex"]

    for case in df["npSchema-caseID"].unique():
        case_df = df[df["npSchema-caseID"] == case]
        r = case_df.iloc[0]

        case_regions = sorted(list(case_df["npSchema-region"].unique()))

        row = [r["npClinical-Braak Stage"]]

        if regions == case_regions:
            # Add the cases
            for region in regions:
                r = case_df[case_df["npSchema-region"] == region].iloc[0]

                for stat in stats:
                    row.append(r[stat])

        test_data.append(row)

    cols = ["Braak NFT Stage"]

    for region in regions:
        for stat in stats:
            cols.append(f"{stat.split('-attributes-stats-')[-1]} ({region})")

    test_data = DataFrame(test_data, columns=cols)
    test_data = test_data.fillna(0)

    X_test = test_data[selected_features].to_numpy()
    y_test = (
        test_data["Braak NFT Stage"]
        .map({"0": 0, "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6})
        .tolist()
    )

    y_test_pred = rfc.predict(X_test)
    cm = confusion_matrix(y_test, y_test_pred)
    k = cohen_kappa_score(y_test, y_test_pred, weights="quadratic")

    cm = DataFrame(cm, index=stages, columns=stages)

    # df = px.data.medals_wide(indexed=True)  # replace with your own data source
    fig = px.imshow(cm, text_auto=True, labels=dict(x="Predicted", y="True"))

    fig.update_layout(title=f"Cohen's kappa = {k:.2f}", title_x=0.5)

    return dcc.Graph(figure=fig)


@callback(
    Output("report-div", "children"),
    Input("report-dropdown", "value"),
    State("report-store", "data"),
    suppress_initial_call=True,
)
def return_report_div(selected_report, data):
    """This callback returns a div, which is the figure and table you want to
    show for PPC report.

    """
    if data.get("docs"):
        if selected_report in ("counts", "stage-boxplot"):
            return counts_histogram_layout(data["docs"])
        elif selected_report == "braak-cm":
            return get_confusion_matrix(data["docs"])
        else:
            return html.Div("This report is not currently available.")
    else:
        return html.Div()


@callback(
    Output("counts-histogram", "children"),
    [
        Input("counts-histogram-region", "value"),
        Input("counts-histogram-stat", "value"),
    ],
    State("report-store", "data"),
    State("report-dropdown", "value"),
    suppress_initial_call=True,
)
def plot_counts_histogram(region, stat, data, selected_report):
    """Plot a stacked bar plot of Pre-NFT & iNFT counts for each WSI in a region"""
    df = json_normalize(data["docs"], sep="-")

    df = df[df["npSchema-region"] == region]

    # Reformat the dataframe.
    plot_df = []

    for _, r in df.iterrows():
        if stat.endswith("_count"):
            plot_df.append(
                [
                    r["npSchema-caseID"],
                    "Pre-NFT",
                    r[f"annotation-attributes-stats-PreNFT{stat}"],
                    r["npClinical-Braak Stage"],
                ]
            )
        else:
            plot_df.append(
                [
                    r["npSchema-caseID"],
                    "Pre-NFT",
                    r[f"annotation-attributes-stats-Pre-NFT{stat}"],
                    r["npClinical-Braak Stage"],
                ]
            )

        plot_df.append(
            [
                r["npSchema-caseID"],
                "iNFT",
                r[f"annotation-attributes-stats-iNFT{stat}"],
                r["npClinical-Braak Stage"],
            ]
        )

    if stat.startswith("_"):
        stat = stat[1:]

    stat = stat.strip()

    plot_df = DataFrame(plot_df, columns=["Case", "Type", stat, "Braak NFT Stage"])

    if selected_report == "counts":
        fig = px.histogram(plot_df, x=stat, color="Type")
    else:
        # Subset to only Braak NFT Stage rows.
        plot_df = plot_df[plot_df["Braak NFT Stage"].isin(stages)]

        print("length of plot df", len(plot_df))
        fig = px.box(
            plot_df,
            x=f"Braak NFT Stage",
            y=stat,
            color="Type",
            # points=False,
        )

        fig.update_xaxes(
            categoryorder="array",
            categoryarray=stages,
        )

    return dcc.Graph(figure=fig)
