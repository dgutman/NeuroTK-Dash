import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
import plotly.graph_objects as go
from ..utils.api import get_item_rois, getThumbnail, get_largeImageInfo
import numpy as np
import plotly.express as px
import dash.dcc as dcc
"""Annotation pulling code goes here.."""


# # added by ek ------------------------------------------
beils_image_id = "641bfd93867536bb7a236b9a" 
# # ------------------------------------------------------

def plotImageAnnotations(imageId, annotationName="ManualGrayMatter"):
    """Given an image ID, will plot available annotations.. in the future this will
    maybe be fancier and we can select which annotation to draw if there are several.. but this requires
    a separate panel and gets more complicated"""
    imageId = "641bfd93867536bb7a236b9a" 
   
    rois = get_item_rois(imageId, annotationName)
    annotation_shapes = [np.asarray(val["points"])[..., :2] for val in rois]
    print(len(annotation_shapes))
    baseImage_as_np = getThumbnail(imageId)

    ## The baseimage size is.. here
    print(baseImage_as_np.shape)

    baseImageInfo = get_largeImageInfo(imageId)

    ## Note the weird numpyism of col/row
    x_scale_factor = baseImageInfo['sizeX']/ baseImage_as_np.shape[1]
    y_scale_factor = baseImageInfo['sizeY']/ baseImage_as_np.shape[0]


    annotFig =  go.Figure(px.imshow(baseImage_as_np, color_continuous_scale="gray"))
    for val in annotation_shapes:
        annotFig.add_trace(go.Scatter(x=val[:,0]/x_scale_factor, y=val[:,1]/y_scale_factor))

    return dcc.Graph(figure=annotFig)


