import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots

from datetime import date
from ..utils.helpers import generate_generic_DataTable
from ..utils.api import get_ppc_details_specific, run_ppc
from dash import html, dcc, callback, Output, Input, State


specific_ppc_results_free_text = dmc.TextInput(
    id="specific_table_input",
    label="Provide FolderID",
    placeholder="6464e04c6df8ba8751afabb3",
    style={"width": "auto"},
)
specific_ppc_results_datepicker = dmc.DateRangePicker(
    id="specific_table_daterange",
    label="Provide Date Range",
    minDate=date(1970, 1, 1),  # year, month, day
    value=[date(2023, 6, 22), date(2023, 7, 6)],  # range for Dunn Study replicate
    style={"width": "auto"},
)
specific_ppc_results_region_multiselect = (
    dmc.MultiSelect(
        label="Select Regions of Interest",
        id="specific_table_region_multiselect",
        data=[],
        value=[
            "Frontal cortex",
            "Temporal cortex",
            "Parietal cortex",
            "Occipital cortex",
            "Cingulate cortex",
            "Insular cortex",
            "Hippocampus",
            "Amygdala",
        ],
        clearable=True,
        searchable=True,
    ),
)
specific_ppc_results_stain_multiselect = dmc.MultiSelect(
    label="Select Stains of Interest",
    id="specific_table_stain_multiselect",
    data=[],
    value=["aBeta"],
    clearable=True,
    searchable=True,
)
ppc_params_dict = {
    "specific_ppc_results_hue_value": ["PPC Hue Value", 0.1],
    "specific_ppc_results_hue_width": ["PPC Hue Width", 0.5],
    "specific_ppc_results_saturation_minimum": ["PPC Saturation Minimum", 0.2],
    "specific_ppc_results_intensity_upper_limit": ["PPC Intensity Upper Limit", (197 / 255)],
    "specific_ppc_results_intensity_weak_threshold": ["PPC Intensity Weak Threshold", (175 / 255)],
    "specific_ppc_results_intensity_strong_threshold": ["PPC Intensity Strong Threshold", (100 / 255)],
    "specific_ppc_results_intensity_lower_limit": ["PPC Intensity Lower Limit", 0.0],
}
ppc_params = [
    dmc.NumberInput(
        label=val[0],
        id=key,
        value=val[1],
        precision=2,
        min=0,
        step=0.01,
        max=1,
    )
    for key, val in ppc_params_dict.items()
]
specific_ppc_results_submit_button = dmc.Button(
    "Submit",
    id="specific_table_button",
    n_clicks=None,
    variant="outline",
    compact=True,
    style={"width": "18rem"},
)
specific_ppc_results_datatable = html.Div(
    [],
    className="twelve columns item_datatable",
    id="specific-ppc-results-datatable-div",
)
specific_ppc_results_bar_chart = html.Div(
    [],
    id="specific_table_bar_chart",
)
specific_ppc_results_box_chart = html.Div(
    [],
    id="specific_table_box_chart",
)
specific_absent_ppc_export_button = html.Div(
    [],
    className="twelve columns item_datatable",
    id="specific-absent-ppc-results-export-button-div",
)
specific_absent_ppc_run_button = html.Div(
    [],
    className="twelve columns item_datatable",
    id="specific-absent-ppc-results-run-button-div",
)
specific_absent_ppc_results_datatable = html.Div(
    [],
    className="twelve columns item_datatable",
    id="specific-absent-ppc-results-datatable-div",
)

ppc_results_interface_panel = html.Div(
    [
        dmc.Text(
            "Note that this will work for any folder -- even the generic ADRC collection with FolderID 641bfc52867536bb7a2368a1 which returns an empty DataFrame with the Dunn Study params.",
            size="md",
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(specific_ppc_results_free_text, width="auto"),
                dbc.Col(specific_ppc_results_datepicker, width="auto"),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(specific_ppc_results_stain_multiselect, width="auto"),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(specific_ppc_results_region_multiselect, width="auto"),
            ]
        ),
        html.Br(),
        dbc.Row([dbc.Col(ppc_param, width="auto") for ppc_param in ppc_params]),
        html.Br(),
        dmc.Text(
            "Hit submit without adding/changing any input/default values to return the relevant entries from the Dunn Study folder.",
            size="sm",
            weight=500,
            id="detail_text",
        ),
        html.Br(),
        specific_ppc_results_submit_button,
        specific_ppc_results_datatable,
        html.Br(),
        dbc.Row([dbc.Col(specific_ppc_results_bar_chart, width="auto")]),
        dbc.Row([dbc.Col(specific_ppc_results_box_chart, width="auto")]),
        specific_absent_ppc_results_datatable,
        dbc.Row(
            [
                dbc.Col(specific_absent_ppc_export_button, width="auto"),
                dbc.Col(specific_absent_ppc_run_button, width="auto"),
            ]
        ),
    ]
)


@callback(
    [
        Output("specific_table_region_multiselect", "data"),
        Output("specific_table_stain_multiselect", "data"),
    ],
    [Input("store", "data")],
)
def populate_all_specific_table_multiselects(data):
    data = pd.DataFrame(data)

    region_values = sorted([val for val in data["regionName"].unique().tolist() if val])
    stain_values = sorted([val for val in data["stainID"].unique().tolist() if val])

    return region_values, stain_values


# generates (modified) version of figure 4 from Dunn aBeta PPC paper
def make_stacked_ppc_bar_chart(metadata_df):
    """
    Makes multipanel figure where each panel is a bar chart for a particular stain
    Each bar chart is itself representative of Percent Strong Positive for each region of a particular case
    Which is given as a single bar for each case, subdivided into, and color coded by, region (recreating Dunn fig 4)
    """

    fig = px.bar(
        metadata_df,
        x="caseID",
        y="Percent Strong Positive",
        color="regionName",
        facet_col="stainID",
        category_orders={"stainID": sorted(metadata_df["stainID"].unique())},
        title=f"Percent Strong Positive by Region and Case",
        labels={"caseID": "Case ID", "regionName": "Region", "stainID": "Stain"},
    )
    # NOTE: below update_xaxes can be ommited if desired. only included to force plotly to show all x axis labels
    # if not included, all x axis labels are still there, but some are left out for readability, though will be
    # loaded if a user zooms in to a particular part of the graph or hovers over a given bar
    fig.update_xaxes(tickmode="linear")
    fig.update_layout(xaxis_tickangle=-90)

    return dcc.Graph(figure=fig)


# generates (modified) version of figure 8 from Dunn aBeta PPC paper
def make_ppc_box_chart(metadata_df):
    """
    Makes multipanel figure where each panel is a box chart for a particular diagnostic/staging framework
    """

    metadata_df["Braak Stage"] = metadata_df["Braak Stage"].str.replace("(", "").str.replace(")", "")

    meta_cols = ["caseID", "ABC", "Braak Stage", "CERAD", "Thal", "Percent Strong Positive"]
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
        fig.add_trace(go.Box(x=metadata_df[col].tolist(), y=psp), row=loc[0], col=loc[1])
        fig.update_xaxes(
            categoryorder="array",
            categoryarray=sorted(metadata_df[col].unique()),
            row=loc[0],
            col=loc[1],
        )

    fig.update_layout(showlegend=False, title_text="Percent Strong Positive by Stage of Given Diagnostic Framework")

    return dcc.Graph(figure=fig)


@callback(
    [
        Output("specific-ppc-results-datatable-div", "children"),
        Output("specific-absent-ppc-results-datatable-div", "children"),
        Output("specific-absent-ppc-results-export-button-div", "children"),
        Output("specific-absent-ppc-results-run-button-div", "children"),
        Output("detail_text", "children"),
        Output("specific_table_bar_chart", "children"),
        Output("specific_table_box_chart", "children"),
    ],
    [
        Input("specific_table_button", "n_clicks"),
        State("specific_table_input", "value"),
        State("specific_table_input", "placeholder"),
        State("specific_table_daterange", "value"),
        State("specific_table_region_multiselect", "value"),
        State("specific_table_stain_multiselect", "value"),
    ],
    [
        {key: State(key, "value") for key in ppc_params_dict.keys()},
    ],
    prevent_initial_call=True,
)
def populate_specific_annotations_datatable(
    n_clicks, text_val, text_holder, daterange_val, regions, stains, param_states
):
    folder_id_val = text_val if text_val else text_holder
    param_states = {
        ("_".join(key.split("_")[-2:]) if "intensity" not in key else "_".join(key.split("_")[-3:])): f"{float(val)}"
        for key, val in param_states.items()
    }

    samples_dataset, absent_dataset, counts = get_ppc_details_specific(
        folder_id_val,
        daterange_val,
        regions,
        stains,
        param_states,
    )

    if samples_dataset.empty:
        table = None
    else:
        col_def_dict = {
            "Created On": {
                "field": "Created On",
                "filter": "agDateColumnFilter",
                "filterParams": {"debounceMs": 2500},
                "flex": 1,
                "editable": True,
                "valueGetter": {"function": "d3.timeParse('%Y-%m-%d')(params.data['Created On])"},
            }
        }

        col_defs = [
            ({"field": col} if col not in col_def_dict else col_def_dict[col]) for col in samples_dataset.columns
        ]
        table = generate_generic_DataTable(samples_dataset, id_val="dag-specific-table", col_defs=col_defs)

        col_defs = [
            ({"field": col} if col not in col_def_dict else col_def_dict[col]) for col in absent_dataset.columns
        ]
        absent_table = generate_generic_DataTable(
            absent_dataset, id_val="dag-absent-table", col_defs=col_defs, exportable=True
        )

        export_button = dmc.Button(
            "Export CSV",
            id="absent_table_export_button",
            n_clicks=0,
            variant="outline",
            compact=True,
            style={"width": "18rem"},
        )
        run_button = dmc.Button(
            "Run PPC",
            id="absent_table_run_button",
            n_clicks=0,
            variant="outline",
            compact=True,
            style={"width": "18rem"},
        )
        absent_text = dmc.Text(
            f"Below table shows all items which matched on stainID and regionName, but did not otherwise match PPC Params or which have never had PPC run (total: {absent_dataset.shape[0]}). Scroll below the table and select the 'Export CSV' option for a local copy.",
            size="md",
            weight=500,
        )

        bar_charts = make_stacked_ppc_bar_chart(samples_dataset)
        box_charts = make_ppc_box_chart(samples_dataset)

    return (
        [table],
        [absent_text, absent_table],
        [export_button],
        [run_button],
        f"Showing {counts[0]} of {counts[1]} original, given stain(s) and region(s) criteria provided",
        bar_charts,
        box_charts,
    )


@callback(Output("dag-absent-table", "exportDataAsCsv"), Input("absent_table_export_button", "n_clicks"))
def download_csv(n_clicks):
    if n_clicks:
        return True
    return False


@callback(
    Output("absent_table_run_button", "n_clicks"),
    [
        Input("absent_table_run_button", "n_clicks"),
        State("dag-absent-table", "virtualRowData"),
    ],
    [
        {key: State(key, "value") for key in ppc_params_dict.keys()},
    ],
)
def trigger_ppc(n_clicks, data, param_states):
    data = pd.DataFrame(data)
    # NOTE: pass run=True below to actually submit jobs to be run, otherwise will not submit
    run_ppc(data, param_states)
    return 0
