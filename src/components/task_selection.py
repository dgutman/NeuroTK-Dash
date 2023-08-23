"""
Selection of task through the a dropdown or creating of a new task via a 
button popup window.
"""
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
from dash_mantine_components import Select
from ..utils.settings import gc

task_selection = html.Div(
    [
        dcc.Store(id="task-store", data=[]),
        dbc.Row(
            [
                dbc.Col(
                    html.Div("Select task: ", style={"fontWeight": "bold"}),
                    align="start",
                    width="auto",
                ),
                dbc.Col(html.Div(Select(data=[], id="tasks-dropdown"))),
                dbc.Col(
                    html.Div(
                        html.Button(
                            [html.I(className="fa-solid fa-plus")],
                            title="create new task",
                        ),
                        id="create-task",
                    ),
                    align="end",
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        html.Button(
                            [html.I(className="fa-solid fa-trash")],
                            title="delete selected task",
                            id="delete-task",
                        )
                    ),
                    align="end",
                    width="auto",
                ),
            ]
        ),
    ],
    id="task-selection",
)


@callback(
    [
        Output("tasks-dropdown", "data"),
        Output("tasks-dropdown", "value"),
        Output("tasks-dropdown", "placeholder"),
        Output("delete-task", "disabled"),
    ],
    [
        Input("projects-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def populate_tasks(value):
    """Populate the task dropdown from the value in projects dropdown."""

    tasks = [item["_id"] for item in gc.listFolder(value) if item["name"] == "Tasks"]

    if tasks:
        tasks = [
            {"value": val["name"], "label": val["name"]}
            for val in gc.listItem(tasks[0])
        ]
        return tasks, "", "", False
    else:
        return [], "", "No tasks in project.", True
