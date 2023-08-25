from dash import html, Input, Output, State, callback, dcc, ALL
from ..utils.settings import AVAILABLE_CLI_TASKS
import json
import dash_mantine_components as dmc
import xml.etree.ElementTree as ET

import dash_bootstrap_components as dbc

cli_selector = html.Div(
    [
        dmc.Select(
            label="Select CLI",
            id="cli-select",
            value="PositivePixelCount",
            data=list(AVAILABLE_CLI_TASKS.keys()),
            style={"maxWidth": 300},
        ),
        dmc.Text(id="selected-cli-task"),
    ],
    style={"marginLeft": "30px"},
)


created_component_ids = []  # List to store IDs of created components


### Add a callback so I know which CLI was selected, this will obviously get fancier


@callback(Output("selected-cli-task", "children"), Input("cli-select", "value"))
def show_cli_param_ui(selected_cli_task):
    print(f"You have selected {selected_cli_task}")

    ## Now that I have the xml_content I can also generate a Dash panel
    ## Can refactor this later to either cache things locally and/or pull from the DSA
    ## Each task has an .xml parameter that has the ungoofed up version of the task with less
    ## additional carriage returns and other formatting
    xml_panel, xml_content = generate_slicer_cli_xml_view(selected_cli_task)

    dsa_cli_task_layout = generate_dash_layout_from_slicer_cli(xml_content)

    return [
        html.Div(f"{selected_cli_task} is currently selected"),
        dsa_cli_task_layout,
        # xml_panel,
    ]


def generate_slicer_cli_xml_view(dsa_task_name):
    # Given a DSA task name this will dump the XML document into a panel for debugging

    ## For now assuming the component name matched the XML document

    with open(f"src/components/{dsa_task_name}.xml", "r") as fp:
        xml_content = fp.read().strip()

    # Add the XML display panel
    xml_panel = html.Div(
        [
            html.H3("XML Document"),
            dcc.Textarea(
                id="xml_display",
                value=xml_content,
                style={"width": "100%", "height": 300},
                readOnly=True,  # Make it read-only
            ),
        ]
    )

    return xml_panel, xml_content


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


@callback(
    Output("cliParam-json-output", "children"),
    [Input({"type": "dynamic-input", "index": ALL}, "value")],
    [State({"type": "dynamic-input", "index": ALL}, "id")],
)
def update_json_output(*args):
    # Map names to values
    print("cli params output was triggered")

    names = args[::2]  # Take every other item starting from 0
    values = args[1::2]  # Take every other item starting from 1

    print("Names:", names)
    print("Values:", values)

    result = {value["index"]: name for name, value in zip(names[0], values[0])}

    # Convert the result to a pretty JSON string
    json_string = json.dumps(result, indent=4)
    return json_string


dsa_cli_view_layout = html.Div(
    [
        html.Div(
            id="cliParam-json-output",
            style={"border": "1px solid #ddd", "padding": "10px", "margin-top": "10px"},
        ),
        cli_selector,
        html.Div(json.dumps(AVAILABLE_CLI_TASKS, indent=4)),
    ]
)


# for float_param in param.findall("float"):
#     name = (
#         float_param.find("name").text
#         if float_param.find("name") is not None
#         else ""
#     )
#     label_text = (
#         float_param.find("label").text
#         if float_param.find("label") is not None
#         else ""
#     )
#     default = (
#         float_param.find("default").text
#         if float_param.find("default") is not None
#         else ""
#     )
#     param_components.extend(
#         [
#             html.Label(label_text),
#             dcc.Input(id=name, value=default, type="number", readOnly=False),
#             html.Br(),
#         ]
#     )
