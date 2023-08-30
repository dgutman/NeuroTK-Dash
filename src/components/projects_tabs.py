from dash import html
import dash_mantine_components as dmc

from .projects_frame import projects_frame
from .analysis_frame import analysis_frame
from .ppcAnalysis import ppcRunner_frame

projects_tabs = html.Div([
    dmc.Tabs([
        dmc.TabsList([
            dmc.Tab("Projects", value="projects"),
            dmc.Tab("Analysis", value="analysis"),
        ]),
        dmc.TabsPanel([
            html.Div(
                projects_frame,
            ),
        ], value="projects"),
        dmc.TabsPanel([
            html.Div(
                analysis_frame,
            ),
        ], value="analysis")
    ], orientation="horizontal", value="projects", id='projects-tabs')
])
