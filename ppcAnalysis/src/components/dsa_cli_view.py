from dash import html, Input, Output, State, callback, dcc
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
        ),
        dmc.Text(id="selected-cli-task"),
    ]
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


def generate_dash_layout_from_slicer_cli(xml_string):
    root = ET.fromstring(xml_string)

    ## TO DO:  Hide anything related to DASK and Frame and Style--- this is not reevant

    components = []

    for param in root.findall(".//parameters"):
        param_components = []

        label = param.find("label").text if param.find("label") is not None else ""
        param_components.append(html.H4(label, className="card-title"))

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
                    dcc.Input(id=name, value=default, type="text", readOnly=False),
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
                        id=name,
                        options=[{"label": op, "value": op} for op in options],
                        value=options[0],
                        clearable=False,
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
                        id=name,
                        value=float(default),
                        type="number",
                        step=0.01,
                        readOnly=False,
                        style={"width": "100px"},
                    ),
                    html.Br(),
                ]
            )

            # param_components.extend(
            #     [
            #         html.Label(label_text),
            #         dcc.Input(
            #             id=name, value=default, type="number", step=0.1, readOnly=False
            #         ),
            #         html.Br(),
            #     ]
            # )

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


# data=[{"value": "PositivePixelCount", "label": "PPC"})]])
# ,dmc.Text(id="selected-project")


# Callback to generate the JSON result
# @app.callback(
#     Output('cli_output', 'children'),
#     Input('SubmitCLITask', 'n_clicks'),
#     # Dynamically generate the list of State objects based on created components
#     [State(component_id, 'value') for component_id in created_component_ids]
# )
# def generate_cli_output(n_clicks, *args):
#     if not n_clicks:
#         return ""

#     # Map names to values
#     result = {name: value for name, value in zip(created_component_ids, args)}

#     return html.Pre(json.dumps(result, indent=4))

# project_selector = html.Div(
#     [
#         dmc.Select(
#             label="Select project",
#             placeholder="Select one",
#             id="projects-select",
#             value="evanPPC",  ## Default project
#             data=[
#                 {"value": "evanPPC", "label": "evanPPC"},
#                 {"value": "nftDetector", "label": "NFT Detector"},
#             ],
#             style={"width": 200, "marginBottom": 10},
#         ),
#         dmc.Text(id="selected-value"),
#     ]
# )


dsa_cli_view_layout = html.Div(
    [cli_selector, html.Div(json.dumps(AVAILABLE_CLI_TASKS, indent=4))]
)
