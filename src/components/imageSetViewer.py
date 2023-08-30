""" This will be a viewer that displays one or more related images.. for example all of the images for a specific tissue block"""
import dash_bootstrap_components as dbc
from dash import html
from tqdm import tqdm
from functools import lru_cache
from ..utils.database import fetch_and_cache_image_thumb
from ..utils.settings import DSA_BASE_URL, gc

# This will render a set of thumbnails from a given region or case depending on what input it receives


def genRelatedImagePanel(image_info):
    imageId = image_info["_id"]
    stainId = image_info.get("npSchema", {}).get("stainID", "")
    regionName = image_info.get("npSchema", {}).get("regionName", "")
    image_details = f"{regionName.title()}, Stained with {stainId}"

    image_card_content = create_card_content_withremoteimage(
        image_info["name"], image_info["_id"], image_details
    )

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
    ## This hsould be changed,, right now we are returning a gigantic panel with all of the data being loaded
    ## at once, should just pass a url, or add to  the panel dynamically as things load...
    imageSetViewer_layout = dbc.Row(
        [genRelatedImagePanel(img) for img in imageDataToDisplay]
    )
    return imageSetViewer_layout


## TO DO: MAKE the dataview panel change with a button to change the image size and/or panel size


@lru_cache(maxsize=None)
def create_card_content(name, thumb, image_details, thumb_width=128):
    image = dbc.CardImg(src=thumb, style={"width": thumb_width}, top=True)

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


def get_img_url(imageId, encoding="PNG", height=128):
    ### Given an imageId, turns this into a URL to fetch the image from a girder server
    ## including the token
    thumb_url = f"{DSA_BASE_URL}/item/{imageId}/tiles/thumbnail?encoding={encoding}&height={height}&token={gc.token}"
    return thumb_url


def create_card_content_withremoteimage(name, imgId, image_details):
    image = dbc.CardImg(src=get_img_url(imgId), style={"width": 128}, top=True)

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
