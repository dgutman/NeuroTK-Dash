"""This provide some statistics about what annotations are currently loaded in the database and can further dive into params"""
from dash import html, callback, Input, Output, State
from ..utils.database import getAnnotationNameCount, getUniqueParamSets
import dash_ag_grid as dag
import dash_bootstrap_components as dbc

debug =False 
#### First I will create a control / table that lists all of the annotationNames and counts


getUniqueParamSets("Positive Pixel Count")


def createAnnotationNameCountTable( projectName ):
    """This gets the list of distinct annotation names and returns a table with the numer and names of annotations
    """
    annotationCount = getAnnotationNameCount(projectName)
    
    colDefs = [{"field":"annotationName", "sortable":True,"filter":True, "tooltipField": "annotationName"},
               {"field":"count","headerName":"Count", "sortable":True,"filter":True}
               ]
    
    if debug: print(annotationCount)
    
    paramSets = html.Div(id="paramSet")
    
    annotationCountPanel =  dbc.Row([
        dbc.Col(
        dag.AgGrid(
            id="annotationNameCounts-table",
            rowData=annotationCount,
            defaultColDef={"resizable": True, "sortable": True, "filter": True},
            columnDefs=colDefs,
            columnSize="sizeToFit",
            columnSizeOptions={
                'defaultMinWidth': 200,
                'columnLimits': [{'key':'count','maxWidth': 160}]
            },
            dashGridOptions={"toolTipShowDelay":10,"rowSelection":"single"}
        ),width=5),dbc.Col(paramSets,width=4)])
    # print(annotationCount)

    @callback(Output("paramSet","children"),
          Input("annotationNameCounts-table","selectedRows"))
    def showUniqueParamSets( selected ):
        ##  I only allow one row to be selected, but this call back returns an array..
        if selected:
            print(selected)
            # getUniqueParamSets("Positive Pixel Count")

            paramSets = getUniqueParamSets("Positive Pixel Count")
            print(paramSets)
            return html.Div(selected[0]['annotationName'])
        else:
            return html.Div("No params for this thinger")

    return annotationCountPanel



annotationStats_layout = createAnnotationNameCountTable('evanPPC')