# Imports
from os.path import join, dirname
import dash_bootstrap_components as dbc
from src.components import banner

import dash
from dash import html, dcc, Output, Input, callback
import src.settings as s
from src.components import displayProjects as dp

# from flask import Flask
# import os

# # from src.components.statsGraph import bp as stats_bp, stats_graphs_layout
# from dash_extensions.enrich import DashBlueprint, DashProxy


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
    ],
    title="NeuroTK Dashboard",
)

# Create a tab component.
tab_height = "3vh"
selected_style = {
    "padding": "0",
    "lineHeight": tab_height,
    "fontWeight": "bold",
    "backgroundColor": "#5e2069",
    "color": "#ffffff",
}
tab_style = {
    "padding": "0",
    "lineHeight": tab_height,
    "backgroundColor": "#e297f0",
    "color": "#000000",
}

debug_tab_layout = html.Div("Debug Info")


other_tab_style = dbc.Tabs(
    [
        dbc.Tab(dp.project_tab_layout, label="Project Tab", tab_id="project-tab"),
        dbc.Tab(debug_tab_layout, label="Debug Tab", tab_id="debug-tab"),
    ]
)


project_tabs = html.Div(
    [
        dcc.Tabs(
            id="project-tabs",
            value="projects",
            style={"height": tab_height},
            children=[
                dcc.Tab(
                    label="Projects",
                    value="projects",
                    style=tab_style,
                    selected_style=selected_style,
                ),
                dcc.Tab(
                    label="Dataset",
                    value="dataset",
                    style=tab_style,
                    selected_style=selected_style,
                ),
                dcc.Tab(
                    label="Tasks",
                    value="tasks",
                    style=tab_style,
                    selected_style=selected_style,
                ),
            ],
        ),
        html.Div(id="projects-tab-content"),
    ]
)


def serve_layout():
    """Define the layout of the application."""
    return html.Div(
        [banner(), other_tab_style, project_tabs],
        #         className="app__container",
    )


# Assign the layout to the app.
app.layout = serve_layout()


# Callback function for Selection tab.
@callback(Output("projects-tab-content", "children"), Input("project-tabs", "value"))
def render_content(tab):
    if tab == "projects":
        return html.Div([html.H3("Projects")])
    elif tab == "dataset":
        return html.Div([html.H3("Dataset")])
    elif tab == "tasks":
        return html.Div([html.H3("Tasks")])


if __name__ == "__main__":
    app.run_server(
        # host=APP_HOST,
        # port=APP_PORT,
        debug=True,
        threaded=True
        # dev_tools_props_check=DEV_TOOLS_PROPS_CHECK,
    )
