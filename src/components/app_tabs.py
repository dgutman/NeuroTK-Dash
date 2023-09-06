from dash import html
import dash_mantine_components as dmc

from .projects_tab import projects_frame
from .analysis_tab import analysis_frame
from .jobqueue_tab import jobqueue_frame
from .annotations_tab import annotations_frame

app_tabs = html.Div(
    [
        dmc.Tabs(
            [
                dmc.TabsList(
                    [
                        dmc.Tab("Projects", value="projects"),
                        dmc.Tab("Analysis", value="analysis"),
                        dmc.Tab("Job Queue", value="jobQueue"),
                        dmc.Tab("Annotations", value="annotations"),
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
                        jobqueue_frame,
                    ],
                    value="jobQueue",
                ),
                dmc.TabsPanel(
                    [
                        annotations_frame
                    ], 
                    value="annotations"
                )
            ],
            orientation="horizontal",
            value="projects",
            id="projects-tabs",
        )
    ]
)
