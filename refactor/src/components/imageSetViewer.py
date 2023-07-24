""" This will be a viewer that displays one or more related images.. for example all of the images for a specific tissue block"""
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from ..utils.api import getThumbnail


## We have to pull the images from the DSA and use base64 encoding to actually set them as an iamge source


# def load_image(image_path):
#     image = Image.open(image_path)
#     return np.array(image)




# This will render a set of thumbnails from a given region or case depending on what input it receives

def genRelatedImagePanel( imageInfo ):
    print(imageInfo)
    imageId = imageInfo['_id']



    card = dbc.Card(
        [
            dbc.CardImg(src=getThumbnail(imageId,return_format='b64img'), top=True),
            dbc.CardBody(
                [
                    html.H4(imageInfo['stainID'], className="card-title"),
                    html.P(
                        f"This should be displaying info about the image you clicked {imageInfo['blockID']} {imageInfo['stainID']}",
                        className="card-text",
                    ),
                    dbc.Button("GetAnnotationForThis", color="primary"),
                ]
            ),
        ],
        style={"width": "18rem"},
    )
    return card


def imageSetViewer_layout( imageDataToDisplay ):
    imageSetViewer_layout = dbc.Row([ genRelatedImagePanel(img) for img in imageDataToDisplay])
    return imageSetViewer_layout



