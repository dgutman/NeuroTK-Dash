from dash import html, dcc, Input, Output, State, ALL, callback
from ..utils.settings import AVAILABLE_CLI_TASKS
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import json
import xml.etree.ElementTree as ET
import dash
from ..utils.api import run_ppc
from ..utils.database import insertJobData


## TO DO
## Debating whether I insert stuff directly, or push to
## a jobQueue_store or something.. this is to be determined


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


def create_cli_selector():
    return dbc.Container(
        [
            dcc.Store(id="cliItems_store"),
            dcc.Store(id="curCLI_params", data={}),
            dbc.Button("CLI Testing", id="getCliItems-button"),
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
                            children=[
                                html.Div(id="cli-output"),
                                dbc.Button("Submit CLI", id="submit-cli-button"),
                            ],
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Div("ImageID List for CLI"),
                            dmc.Text(id="imagelist", style=CLI_OUTPUT_STYLE),
                            dmc.Text(id="imageId_List"),
                        ],
                        width=3,
                    ),
                    dcc.Store(id="cliImageList_store"),
                    dbc.Col(
                        dmc.Text(
                            id="cliParam-json-output",
                            style=CLI_OUTPUT_STYLE,
                        ),
                        width=3,
                    ),
                ]
            ),
        ],
        style=CLI_SELECTOR_STYLE,
    )


def generate_xml_panel(xml_content):
    return html.Div(
        [
            html.H3("XML Document"),
            dcc.Textarea(
                id="xml_display",
                value=xml_content,
                style={"width": "100%", "height": 300},
                readOnly=True,
            ),
        ]
    )


### Update this cliItems from the main table data.


## TO DO-- DO NOT ALLOW THE CLI TO bE SUBMITTED IF THERE ARE NO ACTUAL]
## ITEMS TO RUN.. its confusing..


@callback(Output("cliItems_store", "data"), Input("projectItem_store", "data"))
def updateCliTasks(data):
    # print(len(data), "Items should be in the projectCLI Item Store")
    return data


@callback(Output("imagelist", "children"), Input("cliItems_store", "data"))
def displayImagesForCLI(data):
    # print(len(data), "items in imagelist..")
    ## This gets the data from the itemSet store, it really needs to be the
    ## filtered version based on the task you are trying to run, will be integrated
    # print(data[0])
    # print("I like data")
    ## This is what I will dump in the imagelist for now.. will expand over time
    outputData = ""

    if data:
        for i in data[0:10]:
            outputData += f"{i['name']},"

    return html.Div(outputData)


def read_xml_content(dsa_task_name):
    with open(f"src/slicerCLIxmlDocs/{dsa_task_name}.xml", "r") as fp:
        return fp.read().strip()


@callback(Output("selected-cli-task", "children"), Input("cli-select", "value"))
def show_cli_param_ui(selected_cli_task):
    xml_content = read_xml_content(selected_cli_task)
    xml_panel = generate_xml_panel(xml_content)
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


## This will eventually go away.. using this for debugging for now, don't really need to see
# the params


@callback(Output("cliParam-json-output", "children"), Input("curCLI_params", "data"))
def displayCurCLIParamJson(data):
    return json.dumps(data, indent=4)


#    Output("cliParam-json-output", "children"),


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
    components.append(
        html.Button(
            "SubmitCLITask", id="submit-cli-button", className="btn btn-primary"
        )
    )

    # Add an area to display JSON output
    # Currently dumping this into another component..
    components.append(
        html.Div(
            id="cli-output",
            style={
                "border": "1px solid #ddd",
                "padding": "10px",
                "margin-top": "10px",
                "border-radius": "5px",
                "box-shadow": "2px 2px 12px #aaa",
            },
        )
    )

    return dbc.Container(components, className="mt-3")


## Add temporary callback to display the CLI output...
@callback(
    Output("cli-output", "children"),
    Input("submit-cli-button", "n_clicks"),
    Input("curCLI_params", "data"),
    State("cliItems_store", "data"),
)
def submitCLItasks(n_clicks, curCLI_params, itemsToRun):
    ## Eventually this will display the number of jobs or tasks submitted
    ## And also eventually even keep track of job status..
    ## TO DO -- DISABLE The button until the parameters are good?
    # print(curCLI_params)
    # print(itemsToRun[:10])
    ## I also need the list of items to submit..

    maxJobsToSubmit = 20

    if n_clicks:
        print("Should be running PPC on some items")
        ## This should return a list related to the submitted jobs
        if itemsToRun:
            jobList = run_ppc(itemsToRun[:maxJobsToSubmit], curCLI_params)
            # print(len(json.loads(jobList)), "Jobs submitted")
            print("----Returned job list ----")
            print(jobList)
            insertJobData(jobList, "evanPPC")
        else:
            print("No items were set to run..")

        return html.Div(n_clicks)


clis = dbc.Container(
    [
        dbc.Row(create_cli_selector()),
        # html.Div(json.dumps(AVAILABLE_CLI_TASKS, indent=4)),  # This dumps the cli specs as well
    ]
)


##Creatinga temporary callback/box to display information about the images
## That we are planning on using for the
