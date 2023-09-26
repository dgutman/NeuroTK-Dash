from dash import html, dcc
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import xml.etree.ElementTree as ET


def generate_generic_DataTable(df, id_val, col_defs={}, exportable=False):
    col_defs = [{"field": col} for col in df.columns] if not col_defs else col_defs

    dsa_datatable = html.Div(
        [
            dag.AgGrid(
                id=id_val,
                enableEnterpriseModules=True,
                className="ag-theme-alpine-dark",
                defaultColDef={
                    "filter": "agSetColumnFilter",
                    "editable": True,
                    # "flex": 1,
                    "filterParams": {"debounceMs": 2500},
                    "floatingFilter": True,
                    "sortable": True,
                    "resizable": True,
                },
                columnDefs=col_defs,
                rowData=df.to_dict("records"),
                dashGridOptions={"pagination": True, "paginationAutoPageSize": True},
                # columnSize="sizeToFit",
                csvExportParams={
                    "fileName": f"{id_val.replace('-', '_')}.csv",
                }
                if exportable
                else {},
                style={"height": "75vh"},
            ),
        ]
    )

    return dsa_datatable


def generate_dash_layout_from_slicer_cli(
    xml_string,
    paramSetsToIgnore=("Frame and Style", "Dask", "Girder API URL and Key"),
    disabled=False,
    params=None,
):
    if params is None:
        params = {}

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

        param_components.append(html.H4("Inputs", className="card-title"))

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
                        value=params.get(name, default),
                        type="text",
                        readOnly=False,
                        disabled=disabled,
                    ),
                    html.Br(),
                ]
            )

        for region in param.findall("string"):
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
                        value=params.get(name, default),
                        type="text",
                        readOnly=False,
                        disabled=disabled,
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
                        value=params.get(name, options[0]),
                        clearable=False,
                        style={"maxWidth": 300},
                        disabled=disabled,
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
                    dcc.Input(
                        id=name,
                        value=params.get(name, default),
                        type="text",
                        readOnly=False,
                        disabled=disabled,
                    ),
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
                    html.Label(label_text, style={"marginRight": "10px"}),
                    dcc.Input(
                        id={"type": "dynamic-input", "index": name},
                        value=params.get(name, float(default)),
                        type="number",
                        step=0.01,
                        readOnly=False,
                        style={
                            "width": "60px",
                            "textAlign": "right",
                            "border": "1px solid #ccc",
                            "marginRight": "5px",
                            "margin": "2px 2px",  # vertical and horizontal margin
                            "appearance": "number-input",  # for Firefox
                            "MozAppearance": "number-input",  # for older Firefox versions
                            "WebkitAppearance": "number-input",  # for Chrome and modern browsers
                        },
                        disabled=disabled,
                    ),
                    html.Br(),
                ]
            )

        for int_param in param.findall("integer"):
            name = (
                int_param.find("name").text
                if int_param.find("name") is not None
                else ""
            )

            label_text = (
                int_param.find("label").text
                if int_param.find("label") is not None
                else ""
            )

            default = (
                int_param.find("default").text
                if int_param.find("default") is not None
                else ""
            )

            # Validate that the default value is a float
            try:
                int(default)
            except ValueError:
                default = 0

            param_components.extend(
                [
                    html.Label(label_text, style={"marginRight": "10px"}),
                    dcc.Input(
                        id={"type": "dynamic-input", "index": name},
                        value=params.get(name, int(default)),
                        type="number",
                        step=1,
                        readOnly=False,
                        style={
                            "width": "60px",
                            "textAlign": "right",
                            "border": "1px solid #ccc",
                            "marginRight": "5px",
                            "margin": "2px 2px",  # vertical and horizontal margin
                            "appearance": "number-input",  # for Firefox
                            "MozAppearance": "number-input",  # for older Firefox versions
                            "WebkitAppearance": "number-input",  # for Chrome and modern browsers
                        },
                        disabled=disabled,
                    ),
                    html.Br(),
                ]
            )

        components.append(dbc.Card(dbc.CardBody(param_components), className="mb-3"))

    return dbc.Container(components, className="mt-3")
