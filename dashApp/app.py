from dash import Dash, html, dcc, callback, Output, Input, dash_table, State
import dash_bootstrap_components as dbc  ## Useful set of layout widgets
import plotly.express as px
import pandas as pd
import dsaDataTable as ddt
import appHeader
import dash_mantine_components as dmc
import flask, json
import get_sample_dataset as gds
import girder_client

import dbHelpers as dbh

# Data file to use for the demo app
df = pd.read_excel("2021SampleData.xlsx")
## This can / should be switched to a local mongo instance and also have a "reload cache" button


### Set some parameters here... probably should just make the config a class..
with open("config.json", "r") as fp:
    config = json.load(fp)


mode = "localDataFile"  ## or just pull from girder

dsaBaseUrl = config["dsaBaseUrl"]
colsToHide = config["colsToHide"]
colsToShow = config["colsToShow"]

if mode == "localDataFile":
    # with open(config['sampleDataFile'],"r") as fh:
    #     itemSet = json.load(fh)
    itemSet = gds.itemSet
else:
    gc = girder_client.GirderClient(apiUrl=dsaBaseUrl)
    itemSet = list(gc.listItem(config["defaultFolderId"], limit=500))


# Load the datatable into a Dash Friendly Component
dsa_datatable = ddt.generate_dsaDataTable(df)

currentStainHistogram = px.histogram(df, x="npSchema.3")
currentRegionHistogram = px.histogram(df, x="npSchema.2")

dataSetDescriptors = dbc.Row(
    [
        dbc.Col(dcc.Graph(figure=currentStainHistogram), width=4),
        dbc.Col(dcc.Graph(figure=currentRegionHistogram), width=4),
    ]
)

collapse = html.Div(
    [
        dbc.Button(
            "Show Analysis Graphs",
            id="collapse-button",
            className="mb-3",
            color="primary",
            n_clicks=0,
        ),
        dbc.Collapse(
            dbc.Card(dataSetDescriptors),
            id="collapse",
            is_open=False,
        ),
    ]
)

dmc_header = dmc.Header(
    height=60,
    children=[dmc.Text("Company Logo"), dmc.Button("Click Me To Do Something")],
    style={"backgroundColor": "#9c86e2"},
)

# Generate some histograms for the distribution

# server = flask.Flask(__name__)
app = Dash(name=__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
# server = app.server  ## This is needed for gunicorn to work properly

ppcView = dbc.Col(html.Div(id="cur-image-for-ppc"), width=8)


app.layout = html.Div(
    [
        dmc_header,
        appHeader.getAppHeader(),
        dsa_datatable,
        ppcView,
        collapse,
    ]
)


#### CALL BACK FUNCTIONS GO HERE -- NEEDED FOR INTERACTIVITY #####
@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    # [Output("cur-hover-image", "children"), Output("cur-image-for-ppc", "children")],
    [Output("cur-image-for-ppc", "children")],
    [Input("datatable-interactivity", "active_cell")],
    # (A) pass table as data input to get current value from active cell "coordinates"
    [State("datatable-interactivity", "data")],
)
def display_click_data(active_cell, table_data):
    thumbUrl = ""
    if active_cell:
        cell = json.dumps(active_cell, indent=2)
        row = active_cell["row"]
        col = active_cell["column_id"]
        value = table_data[row][col]
        out = "%s\n%s" % (cell, value)
        imgId = table_data[row]["id"]
        # Create an Image From this as well
        #        thumbUrl = f"{dsaBaseUrl}/item/{imgId}/tiles/thumbnail?token={gds.gc.token}"##
        thumbUrl = f"/item/{imgId}/tiles/thumbnail?token={gds.gc.token}"  ##

        thumbImg = gds.gc.get(thumbUrl, jsonResp=False)
        # createPPCPanel(thumbUrl)
        print(thumbUrl)

        return (
            json.dumps(active_cell, indent=2),
            html.Img(src=f"{dsaBaseUrl}{thumbUrl}"),
        ), [html.Div()]
    else:
        return []  ## This needs to change based on number of outputs to main function


## If you get weird docker behavior, make sure things are exposed/bound to 0.0.0.0
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
