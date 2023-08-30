from dash import html, dcc
from .projects_frame import projects_frame
from .analysis_frame import analysis_frame
from .ppcAnalysis import ppcRunner_frame
from .jobQueue import jobQueue_frame

# Parameters used in tabs.
tab_height = "3vh"  # height of tab


# CSS on tab when selected.
selected_style = {
    "padding": "0",
    "lineHeight": tab_height,
    "fontWeight": "bold",
    "backgroundColor": "#5e2069",
    "color": "#ffffff",
}

# CSS on tab when not selected.
tab_style = {
    "padding": "0",
    "lineHeight": tab_height,
    "backgroundColor": "#e297f0",
    "color": "#000000",
}

projects_tabs = html.Div(
    [
        dcc.Tabs(
            id="projects-tabs",
            value="jobQueue",  # Changed default tab
            style={"height": tab_height},
            children=[
                dcc.Tab(
                    label="Projects",
                    value="projects",
                    style=tab_style,
                    selected_style=selected_style,
                    children=[projects_frame],
                ),
                dcc.Tab(
                    label="Analysis",
                    value="analysis",
                    style=tab_style,
                    selected_style=selected_style,
                    children=[analysis_frame],
                ),
                dcc.Tab(
                    label="PPC Data",
                    value="ppc",
                    style=tab_style,
                    selected_style=selected_style,
                    children=[ppcRunner_frame],
                ),
                dcc.Tab(
                    label="Job Queue",
                    value="jobQueue",
                    style=tab_style,
                    selected_style=selected_style,
                    children=[jobQueue_frame],
                ),
            ],
        ),
    ]
)
