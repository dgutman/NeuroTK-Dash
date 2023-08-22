import dash
from dash import Input, Output, State, html, dcc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from PIL import Image
from plotly.subplots import make_subplots
import plotly.express as px
import dash_bootstrap_components as dbc
import requests
import dash_mantine_components as dmc
from src.components.multiChannelView import multiChannelViz_layout
from io import BytesIO

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


pt_cloud_layout = html.Div(
    style={"margin": "0px", "padding": "0px"},
    children=[
        dcc.Graph(
            id="image-with-points",
            style={
                "width": "75%",
                "height": "80%",
                "display": "inline-block",
                "margin": "0px",
                "padding": "0px",
            },
            config={
                "staticPlot": False,
                "displayModeBar": True,
                "modeBarButtonsToAdd": ["drawrect"],
            },
        ),
        dcc.Graph(
            id="bar-chart",
            style={
                "width": "25%",
                "display": "inline-block",
                "vertical-align": "top",
                "margin": "0px",
                "padding": "0px",
            },
        ),
        html.Div(id="hover-data", style={"padding": "20px", "height": "100px"}),
        html.Div(id="selected-roi"),
        dcc.Graph(id="full-resolution-graph", style={"height": "50%"}),
    ],
)

tabs_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Point Cloud Viz", value="ptCloud-tab"),
                dmc.Tab("MultiChannel Viewer", value="multiChannel-tab"),
            ]
        ),
        dmc.TabsPanel(pt_cloud_layout, value="ptCloud-tab"),
        dmc.TabsPanel(multiChannelViz_layout, value="multiChannel-tab"),
    ],
    value="multiChannel-tab",
    variant="pills",
    color="blue",
)

app.layout = tabs_layout


# Load the image using PIL
img = Image.open("sample_image_for_pointdata.png")
width, height = img.size

# Convert the image to a numpy array
img_array = np.array(img)

# Sample points
points = pd.DataFrame(
    {
        "x": [50, 100, 150, 200, 250],
        "y": [50, 100, 150, 200, 600],
        "id": ["A", "B", "C", "D", "E"],
    }
)

num_points = len(points)
random_colors = [
    "#%02x%02x%02x" % (int(r), int(g), int(b))
    for r, g, b in np.random.randint(0, 255, size=(num_points, 3))
]
points["color"] = random_colors


# Create the initial figure with the image and scatter points
@app.callback(
    Output("image-with-points", "figure"), Input("image-with-points", "relayoutData")
)
def update_image(relayoutData):
    fig = make_subplots(rows=1, cols=1, subplot_titles=("Image with Points",))

    # Display image
    fig.add_trace(go.Image(z=img_array), 1, 1)

    # Add scatter points
    fig.add_trace(
        go.Scatter(
            x=points["x"],
            y=points["y"],
            mode="markers",
            marker=dict(size=10, color=points["color"]),
            hoverinfo="text",
            text=points["id"],
        )
    )

    # Update layout to keep the image aspect and set drag mode
    fig.update_layout(
        margin=dict(t=5, b=5, l=2, r=2),  # Adjust these values as needed
        dragmode="drawrect",
        shapes=[],
        # dragmode="select",
    )
    fig.update_xaxes(range=[0, width])
    fig.update_yaxes(range=[0, height], scaleanchor="x")

    return fig


# Show a bar chart with random values when hovering over a point
@app.callback(Output("bar-chart", "figure"), Input("image-with-points", "hoverData"))
def update_bar_chart(hoverData):
    if (
        hoverData
        and "points" in hoverData
        and len(hoverData["points"]) > 0
        and "text" in hoverData["points"][0]
    ):
        point_id = hoverData["points"][0]["text"]
        attributes = np.random.rand(8)
        df = pd.DataFrame(
            {"attributes": [f"Attr{i}" for i in range(1, 9)], "values": attributes}
        )
        fig = px.bar(df, x="attributes", y="values", title=f"ID: {point_id}")
        return fig
    return px.bar(title="Hover over a point")


@app.callback(Output("hover-data", "children"), Input("image-with-points", "hoverData"))
def display_hover_data(hoverData):
    if (
        hoverData
        and "points" in hoverData
        and len(hoverData["points"]) > 0
        and "x" in hoverData["points"][0]
        and "y" in hoverData["points"][0]
    ):
        x = hoverData["points"][0]["x"]
        y = hoverData["points"][0]["y"]
        return f"X: {x}, Y: {y}"
    return "Hover over the image"


@app.callback(
    Output("selected-roi", "children"), Input("image-with-points", "relayoutData")
)
def update_full_res_image(relayout_data):
    # Extract rectangle coordinates

    if "shapes" in relayout_data:
        scale_factor_X = 1
        scale_factor_Y = 1

        x0 = relayout_data["shapes[0].x0"] * scale_factor_X
        x1 = relayout_data["shapes[0].x1"] * scale_factor_X
        y0 = relayout_data["shapes[0].y0"] * scale_factor_Y
        y1 = relayout_data["shapes[0].y1"] * scale_factor_Y

        # Request the full-resolution image section
        # full_res_image_section = request_full_res_image(x0, y0, x1, y1)

        # Create a figure with the full-resolution image
        # fig = px.imshow(full_res_image_section)
        # return fig
        return html.Div(f"{x0},{x1},{y0},{y1}")
    else:
        return html.Div("Nothing selected yet..")


if __name__ == "__main__":
    app.run_server(debug=True)


# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output, State
# import plotly.graph_objects as go
# import numpy as np
# import pandas as pd
# from PIL import Image
# import plotly.express as px

# # Dash app setup
# app = dash.Dash(__name__)

# app.layout = html.Div(
#     [
#         dcc.Graph(
#             id="image-with-points", style={"width": "60%", "display": "inline-block"}
#         ),
#         dcc.Graph(
#             id="bar-chart",
#             style={"width": "30%", "display": "inline-block", "vertical-align": "top"},
#         ),
#         html.Div(id="hover-data", style={"padding": "20px"}),
#     ]
# )


# # # Add image
# # fig.add_layout_image(
# #     dict(
# #         source="https://raw.githubusercontent.com/cldougl/plot_images/add_r_img/vox.png",
# #         xref="paper", yref="paper",
# #         x=1, y=1.05,
# #         sizex=0.2, sizey=0.2,
# #         xanchor="right", yanchor="bottom"
# #     )
# # )
# # Load the image using PIL
# img = Image.open("sample_image_for_pointdata.png")

# width, height = img.size

# # Convert the image to a numpy array and normalize it
# img_array = np.array(img) / 255.0

# # Sample points
# points = pd.DataFrame(
#     {"x": [50, 100, 150, 200], "y": [50, 100, 150, 200], "id": ["A", "B", "C", "D"]}
# )


# # Create the initial figure with the image and scatter points
# @app.callback(
#     Output("image-with-points", "figure"), Input("image-with-points", "relayoutData")
# )
# def update_image(relayoutData):
#     fig = go.Figure()

#     # Display image
#     fig.add_trace(go.Heatmap(z=img_array[::-1], colorscale="gray", showscale=False))

#     # Add scatter points
#     fig.add_trace(
#         go.Scatter(
#             x=points["x"],
#             y=points["y"],
#             mode="markers",
#             marker=dict(size=10),
#             hoverinfo="text",
#             text=points["id"],
#         )
#     )

#     # Update layout to keep the image aspect and set drag mode
#     fig.update_layout(dragmode="select")
#     fig.update_xaxes(range=[0, width])
#     fig.update_yaxes(range=[0, height], scaleanchor="x")

#     return fig


# # Show a bar chart with random values when hovering over a point
# @app.callback(Output("bar-chart", "figure"), Input("image-with-points", "hoverData"))
# def update_bar_chart(hoverData):
#     if hoverData:
#         point_id = hoverData["points"][0]["text"]
#         attributes = np.random.rand(8)
#         df = pd.DataFrame(
#             {"attributes": [f"Attr{i}" for i in range(1, 9)], "values": attributes}
#         )
#         fig = px.bar(df, x="attributes", y="values", title=f"ID: {point_id}")
#         return fig
#     return px.bar(title="Hover over a point")


# # Display X,Y on Hover
# @app.callback(Output("hover-data", "children"), Input("image-with-points", "hoverData"))
# def display_hover_data(hoverData):
#     if hoverData:
#         x = hoverData["points"][0]["x"]
#         y = hoverData["points"][0]["y"]
#         return f"X: {x}, Y: {y}"
#     return "Hover over the image"


# if __name__ == "__main__":
#     app.run_server(debug=True)

# # import dash
# # import dash_core_components as dcc
# # import dash_html_components as html
# # from dash.dependencies import Input, Output, State
# # import plotly.express as px
# # import numpy as np
# # import pandas as pd
# # from PIL import Image


# # app = dash.Dash(__name__)

# # width, height = img.size
# # import plotly.graph_objects as go

# # # Create figure
# # fig = go.Figure()

# # # Constants
# # img_width = 1600
# # img_height = 900
# # scale_factor = 0.5

# # # Add invisible scatter trace.
# # # This trace is added to help the autoresize logic work.
# # fig.add_trace(
# #     go.Scatter(
# #         x=[0, img_width * scale_factor],
# #         y=[0, img_height * scale_factor],
# #         mode="markers",
# #         marker_opacity=0
# #     )
# # )

# # # Configure axes
# # fig.update_xaxes(
# #     visible=False,
# #     range=[0, img_width * scale_factor]
# # )

# # fig.update_yaxes(
# #     visible=False,
# #     range=[0, img_height * scale_factor],
# #     # the scaleanchor attribute ensures that the aspect ratio stays constant
# #     scaleanchor="x"
# # )

# # # Add image
# # fig.add_layout_image(
# #     dict(
# #         x=0,
# #         sizex=img_width * scale_factor,
# #         y=img_height * scale_factor,
# #         sizey=img_height * scale_factor,
# #         xref="x",
# #         yref="y",
# #         opacity=1.0,
# #         layer="below",
# #         sizing="stretch",
# #         source="https://raw.githubusercontent.com/michaelbabyn/plot_data/master/bridge.jpg")
# # )

# # # Configure other layout
# # fig.update_layout(
# #     width=img_width * scale_factor,
# #     height=img_height * scale_factor,
# #     margin={"l": 0, "r": 0, "t": 0, "b": 0},
# # )

# # # Disable the autosize on double click because it adds unwanted margins around the image
# # # More detail: https://plotly.com/python/configuration-options/
# # fig.show(config={'doubleClick': 'reset'})
# # img_array = np.array(img) / 255.0

# # points = pd.DataFrame(
# #     {"x": [50, 100, 150, 200], "y": [50, 100, 150, 200], "id": ["A", "B", "C", "D"]}
# # )
# # fig = px.imshow(img_array)
# # fig.add_scatter(
# #     x=points["x"],
# #     y=points["y"],
# #     mode="markers",
# #     marker=dict(size=10),
# #     hoverinfo="text",
# #     text=points["id"],
# # )
# # print(width, height)

# # app.layout = html.Div(
# #     [
# #         dcc.Graph(
# #             id="image-with-points", style={"width": "60%", "display": "inline-block"}
# #         ),
# #         dcc.Graph(
# #             id="bar-chart",
# #             style={"width": "30%", "display": "inline-block", "vertical-align": "top"},
# #         ),
# #         html.Div(id="hover-data", style={"padding": "20px"}),
# #     ]
# # )


# # @app.callback(Output("bar-chart", "figure"), Input("image-with-points", "hoverData"))
# # def update_bar_chart(hoverData):
# #     if hoverData:
# #         point_id = hoverData["points"][0]["text"]
# #         attributes = np.random.rand(8)
# #         df = pd.DataFrame(
# #             {"attributes": [f"Attr{i}" for i in range(1, 9)], "values": attributes}
# #         )
# #         fig = px.bar(df, x="attributes", y="values", title=f"ID: {point_id}")
# #         return fig
# #     return px.bar(title="Hover over a point")


# # @app.callback(Output("hover-data", "children"), Input("image-with-points", "hoverData"))
# # def display_hover_data(hoverData):
# #     if hoverData:
# #         x = hoverData["points"][0]["x"]
# #         y = hoverData["points"][0]["y"]
# #         return f"X: {x}, Y: {y}"
# #     return "Hover over the image"


# # if __name__ == "__main__":
# #     app.run_server(debug=True)
