"""
Slicer CLIs selection / display panel.
"""
from dash import html, callback, Input, Output, dcc, State
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from ..utils.settings import AVAILABLE_CLI_TASKS
import xml.etree.ElementTree as ET

clis = [{'value': k, 'label': v} for k, v in AVAILABLE_CLI_TASKS.items()]


clis = html.Div(
    [
        dbc.Row([
            dbc.Col(
                html.Div("Select Analysis: ", style={"fontWeight": "bold"}), 
                align="start", 
                width="auto"
            ),
            dbc.Col(
                dmc.Select(
                    id='cli-select', data=clis, value=clis[0]['value'],
                    disabled=False
                )
            )
        ]),
        dbc.Row(html.Div(id='cli-inputs')),
        dbc.Row(html.Button(
            "SubmitCLITask", id="submit-cli-button", className="btn btn-primary"
        )),
        dbc.Row(html.Div(id='temp'))
    ]
)


@callback(
    Output('cli-inputs', 'children'), 
    Input('cli-select', 'value')
)
def create_cli_inputs(cli):
    """
    Return a Div with inputs for the selected CLI.
    """
    # Read the XML file.
    with open(f'src/slicer-cli-xmls/{cli}.xml', "r") as fp:
        xml_string = fp.read().strip()
    
    # Format the XML content.
    root = ET.fromstring(xml_string)

    # From ChatGPT with modifications.
    components = []

    for param in root.findall(".//parameters"):
        param_components = []

        label = param.find("label").text if param.find("label") is not None else ""
        
        # Only do the I/O.
        if label not in ('I/O', 'IO'):
            continue
            
        label = 'Parameters'
    
        param_components.append(html.H4(label, className="card-title"))

        for region in param.findall("region"):
            
            name = region.find("name").text if region.find("name") is not None else ""

            label_text = (
                region.find("label").text + ': ' if region.find("label") is not None else ""
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
                enum.find("label").text + ': ' if enum.find("label") is not None else ""
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
                vector.find("label").text + ': ' if vector.find("label") is not None else ""
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
                float_param.find("label").text + ': '
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

        components.append(dbc.Card(dbc.CardBody(param_components), className="mb-3"))

    return dbc.Container(components, className="mt-3")


def get_xml_params(cli):
    with open(f'src/slicer-clis-xmls/{cli}.xml', "r") as fp:
        xml_string = fp.read().strip()
    
    # Format the XML content.
    root = ET.fromstring(xml_string)

    parameters = []

    for param in root.findall(".//parameters"):
        param_components = []

        label = param.find("label").text if param.find("label") is not None else ""
        
        # Only do the I/O.
        if label not in ('I/O', 'IO'):
            continue

        for region in param.findall("region"):
            parameters.append(region.find("name").text if region.find("name") is not None else "")

        for enum in param.findall("string-enumeration"):
            parameters.append(enum.find("name").text if enum.find("name") is not None else "")

        for vector in param.findall("double-vector"):
            parameters.append(vector.find("name").text if vector.find("name") is not None else "")
            
        for float_param in param.findall("float"):
            parameters.append(
                float_param.find("name").text
                if float_param.find("name") is not None
                else ""
            )

    return parameters


# @callback(
#     [Output('cli-select': 'value'), Output()]
# )
# def populate_cli():
#     """Populate the CLI panel if the task is complete."""


# @callback(
#     Output('temp', 'children'),
#     [Input('submit-cli-button', 'n_clicks'),
#      Input('cli-select', 'value')],
#     State('cli-inputs', 'children'), prevent_initial_call=True
# )
# def temp(n_clicks, cli, value):
#     print(get_xml_params(cli))
#     from pprint import pprint
#     temp = value['props']['children'][0]['props']['children']['props']['children']

#     for t in temp:
#         if 'props' in t and 'id' in t['props']:
#             print(t['props']['id'])
#     return html.Div()