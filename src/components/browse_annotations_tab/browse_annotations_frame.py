from dash import html, Input, Output, State, dcc, callback_context, callback
import dash, json
import plotly.graph_objects as go

# from ...utils.api import get_item_rois, pull_thumbnail_array, get_largeImageInfo
import numpy as np
import plotly.express as px
import dash.dcc as dcc
import pickle
from ...utils.settings import gc, dbConn, USER
import dash_bootstrap_components as dbc
from ...utils.database import getAnnotationNameCount

annotationView_filter = html.Div(
    [
        dbc.Label("Filter Annotation List:"),
        dbc.RadioItems(
            options=[
                {"label": "Show All", "value": "all"},
                {"label": "By Dataset", "value": "byDataset"},
                {
                    "label": "By Task",
                    "value": "byTask",
                },
            ],
            value="byDataset",
            id="annotationFilter-input",
            inline=True,
        ),
    ]
)


browse_annotations_frame = html.Div(
    [
        dbc.Row(
            [
                dbc.Select(id="annotationDocName_select", style={"maxWidth": "300px"}),
                dbc.Select(id="imageName_select", style={"maxWidth": "300px"}),
                annotationView_filter,
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(id="currentSelectedImageAnnotationViewer"), width=6),
                dbc.Col(html.Div(id="taskLevel_stats"), width=3),
            ],
        ),
    ]
)


## Generate another panel to display some stats... Maybe use dash bootstrap cards??
## Styling TBD
@callback(
    Output("taskLevel_stats", "children"),
    Input("filteredItem_store", "data"),
    Input("annotationDocName_select", "value"),
    State("imageName_select", "options"),
)
def generateAnnotationStatsForTask(itemSetData, selected_annotation, imageNameOptions):
    # print(imageNameOptions, "are current image name options..")
    statsDict = {}

    if itemSetData:
        statsDict = {
            "taskImageCount": len(itemSetData),
            "annotationDoc": selected_annotation,
        }

        if imageNameOptions:
            statsDict["imagesWithAnnotations"] = len(imageNameOptions)

    return html.Div(json.dumps(statsDict, indent=2))


@callback(
    Output("imageName_select", "options"),
    Input("filteredItem_store", "data"),
    Input("annotationDocName_select", "value"),
)
def getTaskItemList(itemSetData, selected_annotation):
    """This will create a select box listing the current items selected for processing"""
    if itemSetData and selected_annotation:
        imageNameList = []
        validImageIdList = [x["_id"] for x in itemSetData]
        collection = dbConn["annotationData"]

        itemsWithAnnotation_cursor = collection.find(
            {
                "userName": USER,
                "annotation.name": selected_annotation,
                "itemId": {"$in": validImageIdList},
            },
            projection={"itemId": 1},
        )
        itemsWithAnnotation = [x["itemId"] for x in itemsWithAnnotation_cursor]

        imageOptionList = []
        for r in itemSetData:
            if r["_id"] in itemsWithAnnotation:
                imageOptionList.append(
                    {
                        "label": f'{r["name"]}',
                        "value": r["_id"],
                    }
                )
        return imageOptionList


@callback(
    Output("annotationDocName_select", "options"), Input("filteredItem_store", "data")
)
def getAnnotationDocNames(data):
    ## Add a toggle botton to show all versus showing filter by active task only

    itemIdFilter = [x["_id"] for x in data]

    annotationNameCount = getAnnotationNameCount(USER, itemIdFilter)

    #   filteredItem_store

    if annotationNameCount:
        ## Turn this into a list of optins..
        optionList = []
        for r in annotationNameCount:
            optionList.append(
                {
                    "label": f'{r["annotationName"]} ({r["count"]})',
                    "value": r["annotationName"],
                }
            )
        return optionList
        ## TO DO --- if count and count with elements do not match, maybe I pull them here?
    return [""]


@callback(
    Output("currentSelectedImageAnnotationViewer", "children"),
    Input("annotationDocName_select", "value"),
    Input("imageName_select", "value"),
)
def generateImageWithAnnotationOverlays(annotationDocName, imageId):
    # if annotationDocName:
    #     print(annotationDocName, "was selected for image rendering..")

    if imageId:
        imgFig = plotImageAnnotations(imageId)
    else:
        ## For debugging I have a blank image figure
        imgFig = plotImageAnnotations("646654ff6df8ba8751afdf21")
    ## Could cache the numpy arrays locally, although probably not useful
    return imgFig


"""Annotation pulling code goes here.."""


# 646654ff6df8ba8751afdf21
def plotImageAnnotations(
    imageId, annotationName="ManualGrayMatter", plotSeparateShapes=False
):
    """Given an image ID, will plot available annotations.. in the future this will
    maybe be fancier and we can select which annotation to draw if there are several.. but this requires
    a separate panel and gets more complicated

    By default, I am not going to show every shape individually, although in the future I may want to do
    stats and double check individual shape obhects are actually closed
    What I am talking about is that say we are drawing ROIs or drawing a gray matter boundary.  Even though
    every shape is an ROI, or every shape is gray matter, I could potentially draw them as different polygons
    so I may (or may not) want to merge the shapes into a single labeled object, or keep them separate.
    This will be expanded upon going forward..
    """

    ## TO DO: Cache this?
    pickledItem = gc.get(
        f"item/{imageId}/tiles/thumbnail?encoding=pickle", jsonResp=False
    )

    ## Need to have or cache the baseImage size as well... another feature to add

    baseImage_as_np = pickle.loads(pickledItem.content)
    annotFig = go.Figure(
        px.imshow(baseImage_as_np)
    )  # , color_continuous_scale="gray"))

    imageSizeInfo = gc.get(f"item/{imageId}/tiles")  ### I should probably cache this...

    # if there are no ROIs, no need to do anything but return the image for viz

    imageAnnotationData = list(
        dbConn["annotationData"].find({"itemId": imageId, "userName": USER})
    )
    annotationNames = [x["annotation"]["name"] for x in imageAnnotationData]
    # ## Note the weird numpyism of col/row
    x_scale_factor = imageSizeInfo["sizeX"] / baseImage_as_np.shape[1]
    y_scale_factor = imageSizeInfo["sizeY"] / baseImage_as_np.shape[0]

    for a in imageAnnotationData:
        elementList = a["annotation"]["elements"]
        annotationName = a["annotation"]["name"]
        combinedPtArray = []

        for e in elementList:
            if "points" in e:
                ptArray = np.array(e["points"])[:, :2]

                combinedPtArray.extend(ptArray.tolist())
                combinedPtArray.append([None, None])
                # combinedPtArray.extend(
                #     [None, None]
                # )  ## Add s null element between shapes..
                if plotSeparateShapes:
                    annotFig.add_trace(
                        go.Scatter(
                            x=ptArray[:, 0] / x_scale_factor,
                            y=ptArray[:, 1] / y_scale_factor,
                            name=annotationName,
                        )
                    )
        # except:
        #     print("Something weird here", e)

        # After exiting the loop, remove the last [None, None] (if any) before stacking to create the numpy array
        if combinedPtArray and combinedPtArray[-1] == [None, None]:
            combinedPtArray.pop()

        if combinedPtArray:
            # cpa = np.vstack(combinedPtArray)
            cpa = combinedPtArray
        else:
            cpa = np.array([])
        # print(cmp)

        if len(cpa):
            # print(cpa)
            # if cpa:

            x_values = [
                (pt[0] / x_scale_factor if pt[0] is not None else None) for pt in cpa
            ]
            y_values = [
                (pt[1] / y_scale_factor if pt[1] is not None else None) for pt in cpa
            ]

            ## Maybe add a flag here based on whether I output the merged or the one above..
            annotFig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    name=annotationName + "-merged",
                    mode="lines+markers",
                )
            )

    annotFig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),  # removes margins
        legend=dict(
            x=0.5,
            y=0.1,
            traceorder="normal",
            orientation="h",
            valign="top",
            xanchor="center",
            yanchor="top",
        ),
    )

    return dcc.Graph(figure=annotFig)

    ## May want to eventually add a check that pulls the point data if an item does not have any elements
    ## This is a future enhancement
