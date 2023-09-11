from dash import html, dcc, Input, Output, State, ALL, callback, no_update
from ...utils.settings import AVAILABLE_CLI_TASKS, SingletonDashApp
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import json
from collections import Counter
from typing import List

from ...utils.api import submit_ppc_job, lookup_job_record
from ...utils.settings import gc, USER
from ...utils.helpers import generate_dash_layout_from_slicer_cli
from ...utils.database import getProjectDataset

## Note because of the way I am importing the app object, do NOT use @callback, use app.callback here

curAppObject = SingletonDashApp()
app = curAppObject.app
## I find this very confusing.. but binding to main dash app claass


# Constants
CLI_SELECTOR_STYLE = {"marginLeft": "30px"}
CARD_CLASS = "mb-3"
MT3_CLASS = "mt-3"
CLI_OUTPUT_STYLE = {
    "border": "1px solid #ddd",
    "padding": "10px",
    "marginTop": "10px",
    "borderRadius": "5px",
    "boxShadow": "2px 2px 12px #aaa",
}


cli_button_controls = html.Div(
    [
        html.Button(
            "Submit CLI",
            id="cli-submit-button",
            className="mr-2 btn btn-warning",
            disabled=True,
        ),
        html.Button(
            id="cli-job-cancel-button",
            className="mr-2 btn btn-danger",
            children="Cancel Running Job!",
            disabled=True,
        ),
        dbc.Progress(
            id="job-submit-progress-bar",
            className="progress-bar-success",
            style={"visibility": "hidden"},
        ),
    ],
    className="d-grid gap-2 d-md-flex justify-content-md-begin",
)


def create_cli_selector():
    return dbc.Container(
        [
            dcc.Store(id="cliItems_store"),
            dcc.Store(id="curCLI_params", data={}),
            dcc.Store(id="taskJobQueue_store", data={}),
            dbc.Row(
                [
                    dmc.Select(
                        label="Select CLI",
                        id="cli-select",
                        value="PositivePixelCount",
                        data=list(AVAILABLE_CLI_TASKS.keys()),
                        style={"maxWidth": 300},
                    ),
                    dmc.Select(
                        label="Image Mask Name",
                        id="mask-name-for-cli",
                        value="gray-matter-from-xmls",
                        data=["", "gray-matter-from-xmls", "gray-matter-fixed"],
                        style={"maxWidth": 300},
                    ),
                    html.Button(
                        "Refresh Task Status",
                        id="task-status-button",
                        className="mr-2 btn btn-danger",
                        style={"maxWidth": 300},
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dmc.Text(
                            id="selected-cli-task",
                            children=[html.Div(id="cli-output"), cli_button_controls],
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Div(id="cliItemStats", style=CLI_OUTPUT_STYLE),
                        ],
                        width=3,
                    ),
                    dcc.Store(id="cliImageList_store"),
                    dbc.Col(
                        [
                            dmc.Text(
                                "Other Info Here TBD",
                                style=CLI_OUTPUT_STYLE,
                            ),
                            html.Div(id="cli-output-status"),
                            html.Div(id="debugjobtaskstatus"),
                        ],
                        width=3,
                    ),
                ]
            ),
        ],
        style=CLI_SELECTOR_STYLE,
    )


@callback(
    Output("debugjobtaskstatus", "children"),
    Input("task-status-button", "n_clicks"),
    [State("curCLI_params", "data"), State("cliItems_store", "data")],
    prevent_initial_call=True,
)
def refreshTaskStatus(n_clicks, cliParams, items):
    """Look up the status of each job for this task."""
    ### This will check the dsaJobQueue mongo collection, and given a list of imageID's
    ## and a parameter set, will see what jobs have been run and/or submitted
    if n_clicks:
        status_list = {}

        for item in items:
            # Look up this item.
            status = lookup_job_record(cliParams, USER)

            print(status)

        return html.Div(f"You have clicked this button {n_clicks} times.")


### Update this cliItems from the main table data.
## TO DO-- DO NOT ALLOW THE CLI TO bE SUBMITTED IF THERE ARE NO ACTUAL]
## ITEMS TO RUN.. its confusing..
@callback(Output("cliItems_store", "data"), Input("filteredItem_store", "data"))
def updateCliTasks(filtered_store):
    # If the task is selected, but there is not filtered item store. Then
    return filtered_store if filtered_store else []


@callback(
    Output("cliItemStats", "children"),
    Input("cliItems_store", "data"),
)
def displayImagesForCLI(data):
    # print(len(data), "items in imagelist..")
    ## This gets the data from the itemSet store, it really needs to be the
    ## filtered version based on the task you are trying to run, will be integrated
    ## This is what I will dump in the imagelist for now.. will expand over time
    outputData = "Should show item count..."
    if data:
        ## TO DO ... ADD SOME MORE MATH TO DISPLAY OTHER PROPERTIES
        return html.Div(f"Items in Task List: {len(data)} ")
    else:
        return html.Div()


### This reads the XML files from Disk.. in future could also pull them
## from the DSA items, but this is probably the better way
def read_xml_content(dsa_task_name):
    with open(f"src/slicer-cli-xmls/{dsa_task_name}.xml", "r") as fp:
        return fp.read().strip()


@callback(
    [
        Output("cli-select", "value"),
        Output("mask-name-for-cli", "value"),
        Output("cli-select", "disabled"),
        Output("mask-name-for-cli", "disabled"),
    ],
    [Input("tasks-dropdown", "value"), Input("task-store", "data")],
)
def select_task_cli(selected_task, task_store):
    """When choosing a new task, if the task has already been run then
    switch the CLI select to the correct value.
    """
    if selected_task:
        task = task_store.get(selected_task)

        if task is None:
            raise Exception("Selected task is not in task store, there is a BUG!")

        # Set the cli select and annotation mask dropdown to options if needed.
        meta = task.get("meta", {})

        if meta.get("images"):
            return meta["cli"], meta["roi"], True, True

    return no_update, no_update, False, False


@callback(
    Output("cli-output", "children"),
    [
        Input("cli-select", "value"),
        Input("tasks-dropdown", "value"),
        Input("task-store", "data"),
    ],
    prevent_initial_call=True,
)
def show_cli_param_ui(selected_cli_task, selected_task, task_store):
    xml_content = read_xml_content(selected_cli_task)

    # Default values to send back when on new task.
    params = {}

    # Decide if the UI should be in disabled or enabled.
    if selected_task:
        task = task_store.get(selected_task)

        if task is None:
            raise Exception("Selected task is not in task store, there is a BUG!")

        meta = task.get("meta", {})

        if meta.get("images"):
            if "params" not in meta:
                raise Exception(
                    "Images list saved to task without params, this is a BUG!"
                )

            params = meta["params"]

            disabled = True
        else:
            disabled = False
    else:
        disabled = False

    dsa_cli_task_layout = generate_dash_layout_from_slicer_cli(
        xml_content, disabled=disabled, params=params
    )

    return [dsa_cli_task_layout]


@callback(
    Output("curCLI_params", "data"),
    [Input({"type": "dynamic-input", "index": ALL}, "value")],
    [State({"type": "dynamic-input", "index": ALL}, "id")],
)
def update_json_output(*args):
    names = args[::2]  # Take every other item starting from 0
    values = args[1::2]  # Take every other item starting from 1
    result = {value["index"]: name for name, value in zip(names[0], values[0])}
    return result


@app.long_callback(
    output=[
        Output("cli-output-status", "children"),
        Output("task-store", "data", allow_duplicate=True),
        Output("taskJobQueue_store", "data"),
    ],
    inputs=[
        Input("cli-submit-button", "n_clicks"),
        State("curCLI_params", "data"),
        State("cliItems_store", "data"),
        State("mask-name-for-cli", "value"),
        State("tasks-dropdown", "value"),
        State("task-store", "data"),
    ],
    running=[
        (Output("cli-submit-button", "disabled"), True, False),
        (Output("cli-job-cancel-button", "disabled"), False, True),
        (
            Output("job-submit-progress-bar", "style"),
            {"visibility": "visible", "width": "25vw"},
            {"visibility": "visible", "width": "25vw"},
        ),
    ],
    cancel=[Input("cli-job-cancel-button", "n_clicks")],
    progress=[
        Output("job-submit-progress-bar", "value"),
        Output("job-submit-progress-bar", "label"),
        Output("job-submit-progress-bar", "max"),
    ],
    prevent_initial_call=True,
)
def submitCLItasks(
    set_progress,
    n_clicks: int,
    curCLI_params: dict,
    itemsToRun: List[dict],
    maskName: str,
    selected_task: str,
    task_store: List[dict],
):
    """
    Submit a CLI task - though right now this will only work with ppc.

    Args:
        n_clicks: This is the button to submit CLI task. Check if positive to run.
        curCLI_params: Dictionary of the params in the CLI panel.
        itemsToRun: List of DSA items to run.
        maskName: Name of mask which is used to determine the region to run CLI on.
        selected_task: CLI is tied to a task, this is the current selected task.
        task_store: Selected task is just the task name, not the id of it. The id is
            stored in the task_store.

    """
    if n_clicks:
        task_id = None

        for task in task_store:
            if selected_task == task:
                task_id = task_store[task]["_id"]
                break

        if not task_id:
            raise Exception("Task not found in task store, but alert.")

        # Submit metadata to the task.
        task_metadata = {
            "images": [item["_id"] for item in itemsToRun],
            "cli": "PositivePixelCount",
            "params": curCLI_params,
            "roi": maskName,
        }

        item = gc.addMetadataToItem(task_id, metadata=task_metadata)

        # Update this item on the task store.
        task_store[item["name"]] = item

        # Submit the jobs
        jobSubmitList = []
        n_jobs = len(itemsToRun)

        for i, item in enumerate(itemsToRun):
            jobOutput = submit_ppc_job(item, curCLI_params, maskName)
            jobSubmitList.append(jobOutput)

            jobStatuspercent = ((i + 1) / n_jobs) * 100

            set_progress((str(i + 1), f"{jobStatuspercent:.2f}%", n_jobs))

        # if jobSubmitList:
        #     print(len(jobSubmitList), "jobs submitted.")
        # else:
        #     print("No jobs to submit.")

        submissionStatus = [x["status"] for x in jobSubmitList]
        print(jobSubmitList[0])

        ## Can get the entire jobStatus cleverely..

        currentJobStatusInfo = [x["girderResponse"]["status"] for x in jobSubmitList]
        from collections import Counter

        print(Counter(currentJobStatusInfo))

        return (
            html.Div(
                f"{json.dumps(Counter(submissionStatus))} from a total list of {len(jobSubmitList)}"
            ),
            task_store,
            jobSubmitList,
        )


@callback(
    Output("projectItem_store", "data", allow_duplicate=True),
    Input("cli-submit-button", "n_clicks"),
    [
        State("projects-dropdown", "data"),
        State("projects-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def update_task_list(n_clicks, available_projects, project_id):
    if n_clicks:
        # Update the project list.
        projectItemSet = []

        for project in available_projects:
            if project["value"] == project_id:
                projectName = project["label"]

                projectItemSet = getProjectDataset(
                    projectName, project_id, forceRefresh=True
                )

                return projectItemSet


dsa_cli_view_layout = dbc.Container(
    [
        dbc.Row(create_cli_selector()),
    ]
)


@callback(
    Output("cli-submit-button", "disabled"),
    Input("tasks-dropdown", "value"),
    State("task-store", "data"),
)
def toggle_cli_bn_state(selected_task, task_store):
    """
    Disable the submit CLI button when no task is selected.
    """
    if selected_task:
        # There is a task selected, get this task.
        task = task_store.get(selected_task)

        if task is None:
            raise Exception("Selected task is not in task store, there is a BUG!")

        # DEBUG - always return False
        return False

        # # Check the metadata for images - if it exists then the button should disable.
        # if task.get("meta", {}).get("images"):
        #     return True
        # else:
        #     return False

    return True
