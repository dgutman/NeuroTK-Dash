import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
import dash_core_components as dcc


# Initialize Dash
app = dash.Dash(__name__)


app.layout = html.Div(
    [
        # login section
        dcc.Input(id="url-input", type="text", placeholder="Enter DSA URL..."),
        html.Button("Connect", id="connect-button", n_clicks=0),
        html.Div(id="login-status"),
        # collections display
        html.Div(id="collections-display"),
        # annotated images display
        html.Div(id="annotated-images-display"),
        html.Div(id="dsa-annotated-images"),
    ]
)


# Example callback to handle connecting to DSA
@app.callback(Output("login-status", "children"), Input("connect-button", "n_clicks"), State("url-input", "value"))
def connect_to_dsa(n_clicks, url):
    if n_clicks > 0:
        try:
            # Replace this with actual API interaction code
            response = requests.get(f"{url}/system/check?mode=basic")
            response.raise_for_status()
            return f"DSA: {url}"
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
    return ""


# You'll need additional callbacks to handle getting annotated images, collections, etc.
# They would look similar to the connect_to_dsa callback, but with different API endpoints
# and possibly with different inputs and outputs. The outputs could include the 'children' property
# of the 'collections-display' and 'annotated-images-display' Divs to update their contents.


@app.callback(Output("dsa-annotated-images", "children"), [])
def get_annotated_images():
    baseurl = "YOUR_BASE_URL"
    api_url = f"{baseurl}/annotation/images"
    response = requests.get(api_url, params={"limit": 10}, headers={"Cache-Control": "no-cache"})
    d = response.json()

    element = html.Div(className="folder")
    header = html.Div(className="folder-header", children=[f"{len(d)} images with annotations"])
    header.children = [html.Span(className="fa fa-folder"), html.Span(className="fa fa-folder-open")] + header.children

    contents_container = html.Div(className="folder-contents", style={"display": "none"})
    make_item_list(contents_container, d)

    header_container = html.Div([header, contents_container])
    header_container.callback_map = {}

    return element.children.append(header_container)


@app.callback(Output("dsa-collections", "children"), [])
def get_collections():
    baseurl = "YOUR_BASE_URL"
    api_url = f"{baseurl}/collection"
    response = requests.get(api_url, params={"limit": 0}, headers={"Cache-Control": "no-cache"})
    d = response.json()

    contents = html.Div()
    collections = []

    for collection in d:
        element = html.Div(className="collection folder")
        header = html.Div(className="folder-header", children=[collection["name"]])
        header.children = [
            html.Span(className="fa fa-folder"),
            html.Span(className="fa fa-folder-open"),
        ] + header.children

        contents_container = html.Div(className="folder-contents", style={"display": "none"})

        header_container = html.Div([header, contents_container])
        header_container.callback_map = {}

        element.children.append(header_container)
        collections.append(element)

    contents.children = collections
    return contents


def make_item_list(container, item_list):
    items = [html.Div(className="item", children=[item["name"]], data={"item": item}) for item in item_list]
    container.children = items


if __name__ == "__main__":
    app.run_server(debug=True)
