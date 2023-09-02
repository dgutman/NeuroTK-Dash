from dash import html
import dash_mantine_components as dmc

from .projects_frame import projects_frame
from .analysis_frame import analysis_frame
from .jobQueue import jobQueue_frame

# from .ppcAnalysis import ppcRunner_frame

app_tabs = html.Div(
    [
        dmc.Tabs(
            [
                dmc.TabsList(
                    [
                        dmc.Tab("Projects", value="projects"),
                        dmc.Tab("Analysis", value="analysis"),
                        dmc.Tab("Job Queue", value="jobQueue"),
                    ]
                ),
                dmc.TabsPanel(
                    [
                        html.Div(
                            projects_frame,
                        ),
                    ],
                    value="projects",
                ),
                dmc.TabsPanel(
                    [
                        html.Div(
                            analysis_frame,
                        ),
                    ],
                    value="analysis",
                ),
                dmc.TabsPanel(
                    [
                        html.Div(jobQueue_frame),
                    ],
                    value="jobQueue",
                ),
            ],
            orientation="horizontal",
            value="analysis",
            id="projects-tabs",
        )
    ]
)