from dash import html, dcc, callback, Output, Input, State, dash_table, no_update
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from pandas import DataFrame, json_normalize
import numpy as np
import plotly.express as px

metric_options = [
    "RatioStrongToPixels",
    "RatioTotalToPixels",
    "RatioWeakToPixels",
    "RatioStrongToTotal",
    "NumberPositive",
    "NumberStrongPositive",
    "NumberTotalPixels",
    "NumberWeakPositive",
    "IntensityAverage",
    "IntensityAverageWeakAndPositive",
    "IntensitySumPositive",
    "IntensitySumStrongPositive",
    "IntensitySumWeakPositive",
]

metric_options = [{"value": opt, "label": opt} for opt in metric_options]

score_options = ["ABC", "Braak Stage", "CERAD", "Thal"]

score_options = [{"value": opt, "label": opt} for opt in score_options]

score_order = {
    "ABC": ["0", "1", "2", "3"],
    "Braak Stage": ["0", "I", "II", "III", "IV", "V", "VI"],
    "CERAD": ["0", "1", "2", "3"],
    "Thal": ["0", "1", "2", "3", "4", "5"],
}

valid_scores = ["0", "1", "2", "3", "4", "5", "I", "II", "III", "IV", "V", "VI"]

ppc_report = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    dmc.Select(
                        label="Select figure or table to plot:",
                        id="ppc-report-dropdown",
                        data=[
                            {"value": "results", "label": "Results Table"},
                            {
                                "value": "summary-stats",
                                "label": "Clinical & demographic summary statistics",
                            },
                            {"value": "stacked-barplot", "label": "Stacked Barplot"},
                            {"value": "boxplot", "label": "Region Boxplots"},
                        ],
                        value="results",
                        style={"width": "auto"},
                    ),
                ),
                dbc.Col(
                    dmc.Button(
                        "Export Results as CSV",
                        color="info",
                        className="me-1",
                        id="export-results-bn",
                    )
                ),
            ]
        ),
        html.Div(id="ppc-report-div"),
        html.Div(id="bn-test"),
    ]
)


def get_results_table(data):
    """Get the results table, allowing saving."""
    df = json_normalize(data, sep="-").fillna(value="").astype(str)

    return html.Div(
        [
            dash_table.DataTable(
                df.to_dict("records"),
                [{"name": i, "id": i} for i in df.columns],
                export_format="csv",
            )
        ]
    )


def get_summary_stats_table(data):
    """Return a data table div to display as the report.

    The input data is in json dictionary format.

    """
    if len(data):
        # Format the data into a dataframe.
        df = []

        clinical_dx = {"AD": 0, "ALS": 0, "other": 0}
        age_at_onset = 0
        age_at_death = 0
        duration = 0
        gender = {"f": 0, "m": 0}
        race = {"b": 0, "w": 0, "other": 0}

        # Format the data into a dataframe.
        df = json_normalize(data, sep="-")

        clin_dx_count = {"AD": 0, "ALS": 0, "other": 0}
        age_at_onset = []
        age_at_death = []
        duration = []
        gender = {"f": 0, "m": 0}
        race = {"b": 0, "w": 0, "other": 0}

        # Iterate by unique case.
        for case in df["npSchema-caseID"].unique():
            case_df = df[df["npSchema-caseID"] == case]

            r = case_df.iloc[0]
            dx = r["npClinical-Clin Dx"]

            if "AD" in dx:
                clin_dx_count["AD"] += 1
            elif "ALS" in dx:
                clin_dx_count["ALS"] += 1
            else:
                clin_dx_count["other"] += 1

            try:
                age = float(r["npClinical-Age at Onset"])
                age_at_onset.append(age)
            except:
                pass

            try:
                age = float(r["npClinical-Age at Death/Bx"])
                age_at_death.append(age)
            except:
                pass

            try:
                age = float(r["npClinical-Duration (years)"])
                duration.append(age)
            except:
                pass

            if r["npClinical-Sex"].lower() == "m":
                gender["m"] += 1
            elif r["npClinical-Sex"].lower() == "f":
                gender["f"] += 1

            case_race = r["npClinical-Race"]

            if case_race == "Caucasian":
                race["w"] += 1
            elif case_race == "Black / African American":
                race["b"] += 1
            else:
                race["other"] += 1

        table_data = {
            "Clinical variable": [
                "Clinical diagnosis",
                "Age at onset, mean (SD)",
                "Age at death, mean (SD)",
                "Duration of disease, mean (SD)",
                "Gender",
                "Race",
            ],
            "Description": [
                f"AD (n={clin_dx_count['AD']}), ALS (n={clin_dx_count['ALS']}), other dementia (n={clin_dx_count['other']})",
                f"{np.mean(age_at_onset):.2f} ({np.std(age_at_onset):.2f})",
                f"{np.mean(age_at_death):.2f} ({np.std(age_at_death):.2f})",
                f"{np.mean(duration):.2f} ({np.std(duration):.2f})",
                f"{gender['f']} female / {gender['m']} male",
                f"{race['b']} black / {race['w']} white / {race['other']} other",
            ],
        }

        table_data = DataFrame(table_data)
    else:
        # No data so just return an empty table.
        table_data = DataFrame(columns=["Clinical variable", "Description"])

    table_data.to_csv("test.csv")
    return html.Div(
        [
            dash_table.DataTable(
                table_data.to_dict("records"),
                [{"name": i, "id": i} for i in table_data.columns],
                export_format="csv",
            )
        ]
    )


def get_stacked_barplot():
    """Plot a stacked bar plot, where the stacked bars represent each region,
    the y-value is statistics (e.g. ratio strong positive, ratio weak positive,
    etc.) and the x-values are the patients / cases.

    The input data is a JSON dict.

    """
    # There should be a single select, which allows selecting statistic to plot
    # on the y-axis.
    return html.Div(
        [
            dmc.Select(
                label="Select y-axis metric:",
                id="ppc-stacked-dropdown",
                data=metric_options,
                value="RatioStrongToPixels",
                style={"width": "auto"},
            ),
            html.Div(id="ppc-stacked-div"),
        ]
    )


def get_boxplot(data):
    """Box plot of metric grouped by a semi-quantitative score, for specific
    regions.

    """
    if data:
        # Create the layout for plot.
        df = json_normalize(data, sep="-")

        # Get the region list.
        regions = [
            {"value": region, "label": region}
            for region in df["npSchema-region"].unique()
        ]

        if not len(regions):
            return html.Div("No regions available in the data to plot.")

        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dmc.Select(
                                label="Select y-axis metric:",
                                id="metric-dropdown",
                                data=metric_options,
                                value=metric_options[0]["value"],
                                style={"width": "auto"},
                            ),
                        ),
                        dbc.Col(
                            dmc.MultiSelect(
                                label="Select region:",
                                id="region-dropdown",
                                data=regions,
                                value=[regions[0]["value"]],
                                style={"width": "auto"},
                            ),
                        ),
                        dbc.Col(
                            dmc.Select(
                                label="Select score:",
                                id="score-dropdown",
                                data=score_options,
                                value=score_options[0]["value"],
                                style={"width": "auto"},
                            ),
                        ),
                    ]
                ),
                html.Div(id="boxplot-div"),
            ]
        )
    else:
        return html.Div("No data to plot.")


@callback(
    Output("ppc-stacked-div", "children"),
    Input("ppc-stacked-dropdown", "value"),
    State("report-store", "data"),
)
def update_stacked_barplot(selected_metric, report_store):
    """Update the stacked barplot based on the selected metric."""
    if len(report_store):
        df = json_normalize(report_store["docs"], sep="-")

        df = df.sort_values(by="npClinical-Thal")
        case_order = list(df["npSchema-caseID"].unique())

        fig = px.bar(
            df,
            x="npSchema-caseID",
            y=f"annotation-attributes-stats-{selected_metric}",
            color="npSchema-region",
            facet_col="npSchema-stainID",
            category_orders={
                "npSchema-stainID": sorted(df["npSchema-stainID"].unique())
            },
            title=f"{selected_metric} by Region and Case",
            labels={
                "npSchema-caseID": "Case ID",
                "npSchema-region": "Region",
                "npSchema-stainID": "Stain",
            },
        )

        fig.update_xaxes(tickmode="linear")
        fig.update_layout(xaxis_tickangle=-90)
        fig.update_xaxes(categoryorder="array", categoryarray=case_order)

        return dcc.Graph(figure=fig)
    else:
        return html.Div("No data to plot.")


@callback(
    Output("ppc-report-div", "children"),
    Input("ppc-report-dropdown", "value"),
    State("report-store", "data"),
    suppress_initial_call=True,
)
def return_report_div(ppc_selected_report, data):
    """This callback returns a div, which is the figure and table you want to
    show for PPC report.

    """
    if data.get("docs"):
        if ppc_selected_report == "results":
            return get_results_table(data["docs"])
        elif ppc_selected_report == "summary-stats":
            return get_summary_stats_table(data["docs"])
        elif ppc_selected_report == "stacked-barplot":
            return get_stacked_barplot()
        elif ppc_selected_report == "boxplot":
            return get_boxplot(data["docs"])
        else:
            return html.Div("This report is not currently available.")
    else:
        return html.Div()


@callback(
    Output("boxplot-div", "children"),
    [
        Input("metric-dropdown", "value"),
        Input("region-dropdown", "value"),
        Input("score-dropdown", "value"),
    ],
    State("report-store", "data"),
    suppress_initial_call=True,
)
def update_boxplot(metric, regions, score, data):
    """Update the boxplot based on the metric and region selected."""
    # Report store might be empty.
    df = json_normalize(data.get("docs", []), sep="-")

    df = df[df["npSchema-region"].isin(regions)]
    df = df[df[f"npClinical-{score}"].isin(valid_scores)]

    fig = px.box(
        df,
        x=f"npClinical-{score}",
        y=f"annotation-attributes-stats-{metric}",
        points=False,
    )

    fig.update_xaxes(
        categoryorder="array",
        categoryarray=score_order[score],
    )

    return dcc.Graph(figure=fig)
