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

thumbit = get_thumbnail_as_b64(imgId)
# print(thumbit[0:200])
thumb_url = styled_image + f"/tiles/thumbnail"  # ?width=1024"

# params = {"width": 1024}
response = requests.get(thumb_url)

web_img = Image.open(BytesIO(response.content))

multiChannelViz_layout = html.Div(
    [
        dcc.Graph(
            id="web-image",
            style={"width": "75%", "display": "inline-block", "vertical-align": "top"},
        ),
        dbc.Button("Pick Frame Color", id="pick-frame-color"),
    ]
)


example_style = {
    "bands": [
        {"framedelta": 3, "palette": "#FF00FF"},
        {"framedelta": 4, "palette": "#00FFFF"},
        {"framedelta": 5, "palette": "#FF8000"},
    ]
}

simpleThumb = {
    "bands": [
        {"frame": 0, "palette": ["#000000", "#0000ff"], "min": "auto", "max": "auto"},
        {"frame": 1, "palette": ["#000000", "#00ff00"], "max": "auto"},
        {"frame": 2, "palette": ["#000000", "#ff0000"], "max": "auto"},
    ]
}

print("This is the simple thumb. no?")
print(simpleThumb)


@callback(
    Output("web-image", "figure"),
    [
        Input("pick-frame-color", "n_clicks")
    ],  # This can be any input triggering the image update
)
def update_web_image(trigger_value):
    # img_array = np.array(web_img)
    # print("I indeed was clicked.., and am passing", simpleThumb)
    np_thumb = pull_thumbnail_array(imgId, height=1000, style=simpleThumb)
    # print(np_thumb.shape)
    fig = px.imshow(np_thumb)
    return fig


# style: {"bands":[{"framedelta":3,"palette":"#FF00FF"},{"framedelta":4,"palette":"#00FFFF"},{"framedelta":5,"palette":"#FF8000"},{"framedelta":6,"palette":"#FF00
# app.layout = html.Div(
#     [
#         dcc.Graph(
#             id="image-with-points", style={"width": "75%", "display": "inline-block"}
#         ),
#         dcc.Graph(
#             id="bar-chart",
#             style={"width": "20%", "display": "inline-block", "vertical-align": "top"},
#         ),
#         html.Div(id="hover-data", style={"padding": "20px"}),
#     ]{"bands":[{"framedelta":3,"palette":"#FF00FF"},{"framedelta":4,"palette":"#00FFFF"},{"framedelta":5,"palette":"#FF8000"},{"framedelta":6,"palette":"#FF0080"}]}
# )
# https://styx.neurology.emory.edu/girder/api/v1/item/6390b28d4da1ec8c4ffd120a/tiles/zxy/4/7/6?edge=crop&frame=18&token=null&style=%7B%22min%22%3A500%2C%22max%22%3A15000%2C%22palette%22%3A%5B%22rgb%280%2C0%2C0%29%22%2C%22rgb%28255%2C0%2C0%29%22%5D%7D
# style: {"min":500,"max":15000,"palette":["rgb(0,0,0)","rgb(255,0,0)"]}
