import plotly.graph_objects as go
from ..utils.api import get_item_rois, pull_thumbnail_array, get_largeImageInfo
import numpy as np
import plotly.express as px
import dash.dcc as dcc

"""Annotation pulling code goes here.."""


def plotImageAnnotations(imageId, annotationName="ManualGrayMatter"):
    """Given an image ID, will plot available annotations.. in the future this will
    maybe be fancier and we can select which annotation to draw if there are several.. but this requires
    a separate panel and gets more complicated"""

    baseImage_as_np = pull_thumbnail_array(imageId)
    annotFig = go.Figure(px.imshow(baseImage_as_np, color_continuous_scale="gray"))

    # if there are no ROIs, no need to do anything but return the image for viz
    if not (rois := get_item_rois(imageId, annotationName)):
        return dcc.Graph(figure=annotFig)

    annotation_shapes = [np.asarray(val["points"])[..., :2] for val in rois]
    # print(len(annotation_shapes))

    ## The baseimage size is.. here
    # print(baseImage_as_np.shape)

    baseImageInfo = get_largeImageInfo(imageId)

    ## Note the weird numpyism of col/row
    x_scale_factor = baseImageInfo["sizeX"] / baseImage_as_np.shape[1]
    y_scale_factor = baseImageInfo["sizeY"] / baseImage_as_np.shape[0]

    for val in annotation_shapes:
        annotFig.add_trace(
            go.Scatter(x=val[:, 0] / x_scale_factor, y=val[:, 1] / y_scale_factor)
        )
    annotFig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),  # removes margins
        legend=dict(
            x=0,
            y=0.5,
            traceorder="normal",
            orientation="h",
            valign="top",
            xanchor="center",
            yanchor="top",
        ),
    )

    return dcc.Graph(figure=annotFig)
