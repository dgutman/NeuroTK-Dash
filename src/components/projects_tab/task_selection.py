"""
Selection of task through the a dropdown or creating of a new task via a 
button popup window.
"""
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
from dash_mantine_components import Select
from typing import List

from ...utils.settings import gc
from .create_task_popup import create_task_popup

task_selection = html.Div(
    [
        dcc.Store(id="task-store", data=""),
        dbc.Row(
            [
                dbc.Col(
                    html.Div("Select task: ", style={"fontWeight": "bold"}),
                    align="start",
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        Select(
                            data=[],
                            id="tasks-dropdown",
                            clearable=True,
                            placeholder="No task selected.",
                        )
                    )
                ),
                dbc.Col(
                    html.Div(
                        html.Button(
                            [html.I(className="fa-solid fa-plus")],
                            title="create new task",
                        ),
                        id="open-create-task-bn",
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
        create_task_popup,
    ],
    id="task-selection",
)


@callback(Output("curTask_disp", "children"), Input("tasks-dropdown", "value"))
def update_current_task(selected_task):
    if selected_task:
        return html.Div(
            ["Current task: ", html.Strong(selected_task)], style={"color": "#fcfcfc"}
        )
    else:
        return html.Div(
            ["Current task: ", html.Strong("no task selected")],
            style={"color": "#fcfcfc"},
        )


@callback(
    [
        Output("tasks-dropdown", "data"),
        Output("tasks-dropdown", "value"),
        Output("create-task-alert", "hide"),
        Output("new-task-name", "value"),
        Output("create-task-popup", "is_open", allow_duplicate=True),
        Output("create-task-alert", "children"),
        Output("task-store", "data"),
    ],
    [Input("projects-dropdown", "value"), Input("create-task-bn", "n_clicks")],
    State("new-task-name", "value"),
    State("tasks-dropdown", "value"),
    State("create-task-popup", "is_open"),
    prevent_initial_call=True,
)
def populate_tasks(
    project_id: str, n_clicks: int, new_task_name: str, current_task: str, is_open: bool
) -> (List[dict], str, bool, bool, str, bool, str):
    """
    Populate the task dropdown, including creating a new task.

    Args:
        project_id: The selected project (DSA id) in the projects dropdown.
        n_clicks: Number of times the button to create new task has been
            clicked.
        new_task_name: The name of the task to be created, when the create
            new task window is open and the button has been clicked.
        current_task: The currently selected task.
        is_open: True to (keep) open the create task popup window or False to
            (keep) close.

    Returns:
        Data to go in task dropdown.
        Task to be selected.
        True or False to disable delete task button.
        True or False to hide the create task alert.
        Name to show on the create task input box.
        True or False to open or close create task window.
        Message to include in create task alert.

    """
    # Default returns.
    hide = True  # state of create task alert message
    returned_name = ""  # name to display in the create task input box
    alert_message = ""  # message to pass to the create task alert
    selected_task = ""  # task that should be selected

    if n_clicks and is_open:
        # If create task button has been clicked before and the window is open.
        # Create Tasks folder if it does not exist.
        tasks_fld = gc.createFolder(project_id, "Tasks", reuseExisting=True)

        # Grab list of current task item names.
        tasks = {item["name"]: item for item in gc.listItem(tasks_fld["_id"])}

        if new_task_name in tasks:
            # Task exists, switch default return values.
            hide = False  # hide alert
            is_open = True  # keep create task window open
            returned_name = new_task_name  # keep existing name
            alert_message = f'"{new_task_name}" task already exists.'
            selected_task = no_update  # don't change the selected task
        else:
            # Create the new task item.
            tasks[new_task_name] = gc.createItem(tasks_fld["_id"], new_task_name)
            selected_task = new_task_name  # switch selected task to new task
            is_open = False  # close the create task window
    elif project_id:
        # Project has been switched, get new task list.
        tasks_fld = gc.createFolder(project_id, "Tasks", reuseExisting=True)
        tasks = {item["name"]: item for item in gc.listItem(tasks_fld["_id"])}
    else:
        # No project selected.
        tasks = {}

    # Format the tasks to go in a dmc.Select data.
    if tasks:
        options = [{"value": task, "label": task} for task in tasks]
        selected_task = options[1]["value"]  ## This is where we hard code tasks

        return (
            options,
            selected_task,
            hide,
            returned_name,
            is_open,
            alert_message,
            tasks,
        )
    else:
        return [], selected_task, hide, returned_name, is_open, alert_message, []
