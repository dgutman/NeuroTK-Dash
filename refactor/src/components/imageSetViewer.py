""" This will be a viewer that displays one or more related images.. for example all of the images for a specific tissue block"""
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from ..utils.api import get_thumbnail_as_b64

# This will render a set of thumbnails from a given region or case depending on what input it receives


def genRelatedImagePanel(imageInfo):
    imageId = imageInfo["_id"]

    stainId = imageInfo["stainID"]
    regionName = imageInfo["regionName"]
    image_details = f"{regionName.title()}, Stained with {stainId}"

    card = dbc.Col(
        [
            dbc.Card(
                [
                    dbc.CardImg(src=get_thumbnail_as_b64(item_id=imageId), top=True),
                    dbc.CardBody(
                        [
                            html.H4(imageInfo["stainID"], className="card-title"),
                            html.P(image_details, className="card-text"),
                            dbc.Row(
                                [
                                    dmc.Button(
                                        "Get Annotation(s)",
                                        n_clicks=None,
                                        variant="outline",
                                        compact=True,
                                        style={"width": "18rem"},
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                style={"width": "18rem"},
            )
        ],
        width="auto",
    )
    return card


def imageSetViewer_layout(imageDataToDisplay):
    imageSetViewer_layout = dbc.Row([genRelatedImagePanel(img) for img in imageDataToDisplay])
    return imageSetViewer_layout
