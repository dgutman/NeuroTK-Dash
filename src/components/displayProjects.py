from dash import html, dcc, callback, Input, Output, State, ALL, callback_context, MATCH
from src import settings
import dash_bootstrap_components as dbc
from src.settings import (
    gc,
)  ## Getting the girder client with token if DSAKEY is set in environment


## Let's pull a list of sample projects to get started...
if settings.DEBUG_MODE:
    ### Go to the girder client and pull a default list of projects to display
    projList = list(gc.listFolder(settings.SAMPLE_PROJECT_FOLDER))

else:
    projList = None


project_tab_layout = html.Div(
    [
        dcc.Store(id="project-store", data=projList),
        html.Div("Project Summary Info", id="proj-summary-status"),
        html.Div("ListGroupStatus", "list-group-whathappened"),
        html.Div(id="project-list-group-container"),
    ],
    id="project-layout",
)


@callback(
    Output("project-list-group-container", "children"), Input("project-store", "data")
)
def outputProjectListGroup(data):
    ### Given a list of folders i.e. projecst from the DSA api this will generate a component

    listElements = []

    for p in data:
        listElements.append(
            dbc.ListGroupItem(
                dbc.Button(
                    p["name"], id={"type": "projectListElement", "projFolder": p["_id"]}
                )
            )
        )

    return dbc.ListGroup(listElements, id="project-list-group")


@callback(
    Output("list-group-whathappened", "children"),
    [Input({"type": "projectListElement", "projFolder": ALL}, "n_clicks")],
)
def whatWasClicked(n_clicks):
    trigger = callback_context.triggered[0]
    print(trigger)
    if n_clicks:
        return html.Div(f"you clicked on button {trigger}")


@callback(
    [Output({"type": "projectListElement", "projFolder": MATCH}, "active")],
    Input({"type": "projectListElement", "projFolder": MATCH}, "n_clicks"),
)
def toggle_active(n_clicks):
    print("I WAS TRIGGERED.. GRR")
    if n_clicks % 2 == 1:
        return True
    else:
        return False
