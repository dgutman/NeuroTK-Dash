from dash import html, dcc, Input, Output, State, ALL, callback
from ..utils.settings import AVAILABLE_CLI_TASKS, SingletonDashApp
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import json
import xml.etree.ElementTree as ET
import dash
from ..utils.api import run_ppc, submit_ppc_job

# from ..utils.database import insertJobData


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
    "margin-top": "10px",
    "border-radius": "5px",
    "box-shadow": "2px 2px 12px #aaa",
}


cli_button_controls = html.Div(
    [
        html.Button(
            "Submit CLI",
            id="cli-submit-button",
            className="mr-2 btn btn-warning",
        ),
        html.Button(
            id="cli-job-cancel-button",
            className="mr-2 btn btn-danger",
            children="Cancel Running Job!",
        ),
        html.Progress(
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
            dbc.Row(
                [
                    dmc.Select(
                        label="Select CLI",
                        id="cli-select",
                        value="PositivePixelCount",
                        data=list(AVAILABLE_CLI_TASKS.keys()),
                        style={"maxWidth": 300},
                    )
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
                            html.Div("ImageID List for CLI", style=CLI_OUTPUT_STYLE),
                            html.Div(id="cliItemStats", style=CLI_OUTPUT_STYLE),
                        ],
                        width=3,
                    ),
                    dcc.Store(id="cliImageList_store"),
                    dbc.Col(
                        [
                            # dmc.Text(
                            #     id="cliParam-json-output",
                            #     style=CLI_OUTPUT_STYLE,
                            # ),
                            dmc.Text(
                                "Other Info Here TBD",
                                style=CLI_OUTPUT_STYLE,
                            ),
                            html.Div(id="cli-output-status"),
                        ],
                        width=3,
                    ),
                ]
            ),
        ],
        style=CLI_SELECTOR_STYLE,
    )


### Update this cliItems from the main table data.
## TO DO-- DO NOT ALLOW THE CLI TO bE SUBMITTED IF THERE ARE NO ACTUAL]
## ITEMS TO RUN.. its confusing..


@callback(Output("cliItems_store", "data"), Input("filteredItem_store", "data"))
def updateCliTasks(data):
    if data:
        print(len(data), "Items should be in the projectCLI Item Store")
        return data


@callback(Output("cliItemStats", "children"), Input("cliItems_store", "data"))
def displayImagesForCLI(data):
    # print(len(data), "items in imagelist..")
    ## This gets the data from the itemSet store, it really needs to be the
    ## filtered version based on the task you are trying to run, will be integrated
    ## This is what I will dump in the imagelist for now.. will expand over time
    outputData = "Should show item count..."
    if data:
        ## TO DO ... ADD SOME MORE MATH TO DISPLAY OTHER PROPERTIES
        return html.Div(f"Items in Task List: {len(data)} ")


### This reads the XML files from Disk.. in future could also pull them
## from the DSA items, but this is probably the better way
def read_xml_content(dsa_task_name):
    with open(f"src/slicer-cli-xmls/{dsa_task_name}.xml", "r") as fp:
        return fp.read().strip()


@callback(Output("cli-output", "children"), Input("cli-select", "value"))
def show_cli_param_ui(selected_cli_task):
    xml_content = read_xml_content(selected_cli_task)
    # xml_panel = generate_xml_panel(xml_content)
    dsa_cli_task_layout = generate_dash_layout_from_slicer_cli(xml_content)

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


def generate_dash_layout_from_slicer_cli(
    xml_string, paramSetsToIgnore=["Frame and Style", "Dask"]
):
    root = ET.fromstring(xml_string)

    ## TO DO:  Hide anything related to DASK and Frame and Style--- this is not reevant

    # There are certain parameters that should not be made directly visible in the UI such as a specific image
    ## At least for now...
    paramsToHide = []

    components = []

    for param in root.findall(".//parameters"):
        param_components = []

        label = param.find("label").text if param.find("label") is not None else ""
        if label in paramSetsToIgnore:
            continue
        param_components.append(html.H4(label, className="card-title"))

        ## This loops through all the various parameters, I want to hide image params for now..
        hideImageParam = True
        if not hideImageParam:
            for image in param.findall("image"):
                name = image.find("name").text if image.find("name") is not None else ""
                label_text = (
                    image.find("label").text if image.find("label") is not None else ""
                )
                param_components.extend(
                    [html.Label(label_text), dcc.Upload(id=name), html.Br()]
                )

        for region in param.findall("region"):
            name = region.find("name").text if region.find("name") is not None else ""
            label_text = (
                region.find("label").text if region.find("label") is not None else ""
            )
            default = (
                region.find("default").text
                if region.find("default") is not None
                else ""
            )
            param_components.extend(
                [
                    html.Label(label_text),
                    dcc.Input(
                        id={"type": "dynamic-input", "index": name},
                        value=default,
                        type="text",
                        readOnly=False,
                    ),
                    html.Br(),
                ]
            )

        for enum in param.findall("string-enumeration"):
            name = enum.find("name").text if enum.find("name") is not None else ""
            label_text = (
                enum.find("label").text if enum.find("label") is not None else ""
            )
            options = [elem.text for elem in enum.findall("element")]
            param_components.extend(
                [
                    html.Label(label_text),
                    dcc.Dropdown(
                        id={"type": "dynamic-input", "index": name},
                        options=[{"label": op, "value": op} for op in options],
                        value=options[0],
                        clearable=False,
                        style={"maxWidth": 300},
                    ),
                    html.Br(),
                ]
            )

        for vector in param.findall("double-vector"):
            name = vector.find("name").text if vector.find("name") is not None else ""
            label_text = (
                vector.find("label").text if vector.find("label") is not None else ""
            )
            default = (
                vector.find("default").text
                if vector.find("default") is not None
                else ""
            )
            param_components.extend(
                [
                    html.Label(label_text),
                    dcc.Input(id=name, value=default, type="text", readOnly=False),
                    html.Br(),
                ]
            )
        for float_param in param.findall("float"):
            name = (
                float_param.find("name").text
                if float_param.find("name") is not None
                else ""
            )
            label_text = (
                float_param.find("label").text
                if float_param.find("label") is not None
                else ""
            )
            default = (
                float_param.find("default").text
                if float_param.find("default") is not None
                else ""
            )

            # Validate that the default value is a float
            try:
                float(default)
            except ValueError:
                default = 0

            param_components.extend(
                [
                    html.Label(label_text, style={"margin-right": "10px"}),
                    dcc.Input(
                        id={"type": "dynamic-input", "index": name},
                        value=float(default),
                        type="number",
                        step=0.01,
                        readOnly=False,
                        style={
                            "width": "60px",
                            "textAlign": "right",
                            "border": "1px solid #ccc",
                            "margin-right": "5px",
                            "margin": "2px 2px",  # vertical and horizontal margin
                            "appearance": "number-input",  # for Firefox
                            "MozAppearance": "number-input",  # for older Firefox versions
                            "WebkitAppearance": "number-input",  # for Chrome and modern browsers
                        },
                    ),
                    html.Br(),
                ]
            )

        components.append(dbc.Card(dbc.CardBody(param_components), className="mb-3"))

    # Add a button to trigger CLI task submission
    # components.append(
    #     html.Button(
    #         "Submit CLI Task", id="submit-cli-button", className="btn btn-primary"
    #     )
    # )

    # Add an area to display JSON output
    # Currently dumping this into another component..
    # components.append(
    #     html.Div(
    #         id="cli-output",
    #         style={
    #             "border": "1px solid #ddd",
    #             "padding": "10px",
    #             "margin-top": "10px",
    #             "border-radius": "5px",
    #             "box-shadow": "2px 2px 12px #aaa",
    #         },
    #     )
    # )

    return dbc.Container(components, className="mt-3")


## Add temporary callback to display the CLI output...
@app.long_callback(
    output=Output("cli-output-status", "children"),
    inputs=[
        Input("cli-submit-button", "n_clicks"),
        Input("curCLI_params", "data"),
        State("cliItems_store", "data"),
    ],
    running=[
        (Output("cli-submit-button", "disabled"), True, False),
        (Output("cli-job-cancel-button", "disabled"), False, True),
        (
            Output("job-submit-progress-bar", "style"),
            {"visibility": "visible"},
            {"visibility": "hidden"},
        ),
    ],
    cancel=[Input("cli-job-cancel-button", "n_clicks")],
    progress=[
        Output("job-submit-progress-bar", "value"),
        Output("job-submit-progress-bar", "max"),
    ],
)
def submitCLItasks(set_progress, n_clicks, curCLI_params, itemsToRun):
    if n_clicks:
        print("Entered submit CLI task box  ")
        print(n_clicks)
        maxJobsToSubmit = 10
        jobSubmitList = []
        for i in range(maxJobsToSubmit):
            jobOutput = submit_ppc_job(itemsToRun[i], curCLI_params)
            jobSubmitList.append(jobOutput)

            set_progress((str(i + 1), str(maxJobsToSubmit)))
        print("----Returned job list ----")
        if jobSubmitList:
            print(len(jobSubmitList), "jobs were submitted..")

        else:
            print("No items were set to run..")

        return html.Div(f"{n_clicks} and submited {len(jobSubmitList)}")


dsa_cli_view_layout = dbc.Container(
    [
        dbc.Row(create_cli_selector()),
    ]
)
