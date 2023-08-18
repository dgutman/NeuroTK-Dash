""" This will be a viewer that displays one or more related images.. for example all of the images for a specific tissue block"""
import dash_bootstrap_components as dbc
from dash import html
from tqdm import tqdm
from functools import lru_cache
from ..utils.database import fetch_and_cache_image_thumb

# This will render a set of thumbnails from a given region or case depending on what input it receives


def genRelatedImagePanel(image_info):
    imageId = image_info["_id"]

    stainId = image_info["stainID"]
    regionName = image_info["regionName"]
    image_details = f"{regionName.title()}, Stained with {stainId}"

    if thumb := fetch_and_cache_image_thumb(imageId):
        image_card_content = create_card_content(image_info["name"], thumb, image_details)
    else:
        image_card_content = create_card_content(image_info["name"], None, image_details)

    card = dbc.Col(
        [
            dbc.Card(
                image_card_content,
                id=imageId,
                style={"width": "18rem"},
            )
        ],
        width="auto",
    )
    return card


def generate_imageSetViewer_layout(imageDataToDisplay):
    imageSetViewer_layout = dbc.Row([genRelatedImagePanel(img) for img in tqdm(imageDataToDisplay)])
    return imageSetViewer_layout


@lru_cache(maxsize=None)
def create_card_content(name, thumb, image_details):
    image = dbc.CardImg(src=thumb, top=True)

    card = [
        image,
        dbc.CardBody(
            [
                html.H4(name, className="card-title"),
                html.P(image_details, className="card-text"),
            ]
        ),
    ]

    return card
