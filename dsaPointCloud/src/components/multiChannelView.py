### This will load an image from the DSA server and add a multichannel selector
import dash
from PIL import Image
import requests
from io import BytesIO
from dash import dcc, Input, Output, State, html, callback
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
from ..utils.api import get_thumbnail_as_b64, pull_thumbnail_array

imgId = "649b7993fbfabbf55f16fba4"
DSA_BaseURL = "https://candygram.neurology.emory.edu/api/v1"


# img_url = "https://styx.neurology.emory.edu/girder/api/v1/item/6390b28d4da1ec8c4ffd120a/tiles/zxy/4/7/6?edge=crop&frame=18&token=null&style=%7B%22min%22%3A500%2C%22max%22%3A15000%2C%22palette%22%3A%5B%22rgb%280%2C0%2C0%29%22%2C%22rgb%28255%2C0%2C0%29%22%5D%7D"

styled_image = f"{DSA_BaseURL}/item/{imgId}"

thumb_url = styled_image + f"/tiles/thumbnail"  # ?width=1024"

# params = {"width": 1024}
response = requests.get(thumb_url)
web_img = Image.open(BytesIO(response.content))

# Button to toggle the collapsible panel
toggle_button = dbc.Button(
    "Show Image Info", id="collapse-button", className="mb-3", color="primary"
)


image_info = {
    "frames": [
        {"Frame": 0, "Index": 0},
        {"Frame": 1, "Index": 1},
        {"Frame": 2, "Index": 2},
        {"Frame": 3, "Index": 3},
        {"Frame": 4, "Index": 4},
        {"Frame": 5, "Index": 5},
        {"Frame": 6, "Index": 6},
        {"Frame": 7, "Index": 7},
        {"Frame": 8, "Index": 8},
        {"Frame": 9, "Index": 9},
        {"Frame": 10, "Index": 10},
        {"Frame": 11, "Index": 11},
        {"Frame": 12, "Index": 12},
        {"Frame": 13, "Index": 13},
        {"Frame": 14, "Index": 14},
        {"Frame": 15, "Index": 15},
        {"Frame": 16, "Index": 16},
        {"Frame": 17, "Index": 17},
        {"Frame": 18, "Index": 18},
        {"Frame": 19, "Index": 19},
        {"Frame": 20, "Index": 20},
        {"Frame": 21, "Index": 21},
        {"Frame": 22, "Index": 22},
        {"Frame": 23, "Index": 23},
        {"Frame": 24, "Index": 24},
        {"Frame": 25, "Index": 25},
        {"Frame": 26, "Index": 26},
        {"Frame": 27, "Index": 27},
    ],
    "levels": 8,
    "magnification": None,
    "mm_x": None,
    "mm_y": None,
    "sizeX": 25878,
    "sizeY": 22220,
    "tileHeight": 256,
    "tileWidth": 256,
}

# Format the image information for display
info_content = html.Div(
    [
        html.H5("Image Information"),
        html.P(f"Levels: {image_info['levels']}"),
        html.P(f"Size X: {image_info['sizeX']}"),
        html.P(f"Size Y: {image_info['sizeY']}"),
        html.P(f"Tile Height: {image_info['tileHeight']}"),
        html.P(f"Tile Width: {image_info['tileWidth']}"),
        html.Hr(),
        html.H6("Frames:"),
        # html.Ul(
        #     [
        #         html.Li(f"Frame: {frame['Frame']}, Index: {frame['Index']}")
        #         for frame in image_info["frames"]
        #     ]
        # ),
    ]
)

collapsible_panel = dbc.Collapse(
    dbc.Card(dbc.CardBody(info_content)), id="imageInfo-collapse"
)


multiChannelViz_layout = html.Div(
    [
        dbc.Button("Pick Frame Color", id="pick-frame-color"),
        html.Div(
            [
                html.Div(
                    [
                        toggle_button,
                        collapsible_panel,
                    ],
                    style={
                        "width": "15%",
                        "display": "inline-block",
                        "vertical-align": "top",
                    },
                ),
                dcc.Graph(
                    id="web-image",
                    style={
                        "width": "80%",
                        "margin": "0px",
                        "padding": "0px",
                        "display": "inline-block",
                        "vertical-align": "top",
                    },
                ),
            ],
            style={"display": "flex"},  # This ensures inline display
        ),
    ]
)

# multiChannelViz_layout = html.Div(
#     [
#         html.Div(
#             [
#                 toggle_button,
#                 collapsible_panel,
#             ],
#             style={"width": "20%", "display": "inline-block", "vertical-align": "top"},
#         ),
#         dcc.Graph(
#             id="web-image",
#             style={
#                 "width": "85%",
#                 "margin": "0px",
#                 "padding": "0px",
#                 "display": "inline-block",
#                 "vertical-align": "top",
#             },
#         ),
#         dbc.Button("Pick Frame Color", id="pick-frame-color"),
#     ]
# )

simpleThumb = {
    "bands": [
        {"frame": 0, "palette": ["#000000", "#0000ff"], "min": "auto", "max": "auto"},
        {"frame": 1, "palette": ["#000000", "#00ff00"], "max": "auto"},
        {"frame": 2, "palette": ["#000000", "#ff0000"], "max": "auto"},
    ]
}


@callback(
    Output("web-image", "figure"),
    [
        Input("pick-frame-color", "n_clicks")
    ],  # This can be any input triggering the image update
)
def update_web_image(trigger_value):
    np_thumb = pull_thumbnail_array(imgId, height=1000, style=simpleThumb)
    # print(np_thumb.shape)
    fig = px.imshow(np_thumb)
    fig.update_layout(width=800, height=600, margin=dict(t=5, r=5, b=5, l=2))
    return fig


@callback(
    Output("imageInfo-collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("imageInfo-collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    print("I am collapsing.. no?", n)
    if n:
        return not is_open
    return is_open
