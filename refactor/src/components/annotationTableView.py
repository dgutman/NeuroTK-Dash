### This module creates a layout to view the annotation data from the DSA that is cached locally in a mongo table
## We can add all the filters and fun stuff here related to showing annotations, as well as overlaying annotations on images
### For now we will simply display a datatable... but cooler stuff.. coming soon!
from dash import html, callback, Output, Input, State
from ..utils.api import getAllItemAnnotations
from ..utils.database import insertAnnotationData, getAnnotationData_fromDB

update_annotation_button =    html.Button(
                                                "Update Annotation DataSet",
                                                id="update-annotations-btn",
                                                n_clicks=0,
                                            )


projectName = 'evanPPC'


@callback(Output("annotationData_layout","children"),Input("update-annotations-btn",'n_clicks'))
def updateAnnotationDataFromGirder( n_clicks ):
    ### Project name and annotationName will matter going forward... we ma only want to pull PPC results or something for speed
    
    ### Pull the annotation Data from girder and load it into the mongo database, we will then return a table as well...
    print("How dare thee.. you clicked me...")

    ## This should update the annotations if clicked, otherwise, just get the current data in the database..
    if n_clicks:
        annotationItemSet = getAllItemAnnotations()
        ### Now update the database...
        status = insertAnnotationData(annotationItemSet,projectName)
        print(status)

    annotationItemData = getAnnotationData_fromDB(projectName=projectName)
    print(len(annotationItemData),"HI")

    return None


