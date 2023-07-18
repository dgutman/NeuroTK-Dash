import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL
import requests, json, os
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import girder_client


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
    ],
)

# # Replace with the base URL of your DSA
BASE_URL = "https://styx.neurology.emory.edu/api/v1"
gc = girder_client.GirderClient(apiUrl=BASE_URL)


class DSAFileTree:
    def __init__(self, DSAResoucePath, gc: girder_client.GirderClient, id: str):
        self.resourcePath = DSAResoucePath
        self.gc = gc  ### GirderClient

    def getResourcePathId(self, resourcePath):
        rp = gc.get("/resource/lookup?path=%s" % resourcePath)
        if rp:
            return rp["_id"]
        else:
            return None

    def render(self) -> dmc.Accordion:
        return dmc.AccordionMultiple(
            self.build_tree(self.resourcePath, isRoot=True, parentFolderType="folder"),
        )

    def flatten(self, l):
        return [item for sublist in l for item in sublist]

    def make_file(self, file_name):
        return dmc.Text(
            [DashIconify(icon="akar-icons:file"), " ", file_name],
            style={"paddingTop": "5px"},
        )

    def make_folder(self, folder_name):
        return [
            DashIconify(
                icon="akar-icons:folder",
            ),
            " ",
            folder_name,
        ]

    def list_folder(self, path, parentFolderType="folder"):
        ### list a folder from the DSA
        print("Listing folder", path)
        pathId = self.getResourcePathId(path)

        fldrList = [x["name"] for x in gc.listFolder(pathId, parentFolderType)]
        print(list(fldrList))
        return fldrList

    def get_collection_folders(self, path):
        ### This is the the first thing called and will get all the top level folders..
        pass

    def build_tree(self, path, isRoot=False, parentFolderType="folder"):
        ## Main modification is here.. Will use the girder Path lookup functionality
        ## So this is easier to follow than if using IDs.. can also add a class
        ## to cache the folders .. although not sure if that is particularly useful
        print("Processing path: %s" % path)
        d = []
        if self.getResourcePathId(path):
            # children = [
            #     self.build_tree(os.path.join(path, x), path)
            #     for x in self.list_folder(path, parentFolderType)
            # ]
            # print(children)
            ## Need to think through the logic
            subFolders = [
                os.path.join(path, x) for x in self.list_folder(path, parentFolderType)
            ]
            # if isRoot:
            #     print("Processing root....")
            #     return self.flatten(children)
            folderList = [
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl(
                            self.make_folder(os.path.basename(subFolderPath)),
                            id={
                                "type": "folder-contents",
                                "index": os.path.basename(subFolderPath),
                            },
                        ),
                        dmc.AccordionPanel(html.Div(os.path.basename(subFolderPath))),
                    ],
                    value=subFolderPath,
                )
                for subFolderPath in subFolders
            ]
            return folderList
        else:
            d.append(self.make_file(os.path.basename(path)))

        return d


# Usage
## I am using the DSA resource path it's easier to follow

dsaResourcePath = "/collection/NeuroPathDemoImages/2020"  # Any filepath here

fileTreeLayout = DSAFileTree(dsaResourcePath, gc, "file_tree_root").render()
print(fileTreeLayout)

app.layout = dbc.Row(
    [
        html.Div("DSA Tree Browser for %s" % dsaResourcePath),
        fileTreeLayout,
    ]
)


@app.callback(
    Output({"type": "folder-contents", "index": MATCH}, "children"),
    [Input({"type": "load-button", "index": MATCH}, "n_clicks")],
    [State({"type": "folder-contents", "index": MATCH}, "id")],
)
def load_collection(n, id):
    print("HELLO COLLECTION")
    if n is not None:
        response = requests.get(
            BASE_URL + "/folder",
            params={"parentType": "collection", "parentId": id["index"], "limit": 0},
        )
        folders = response.json()
        return [
            html.Div(
                [
                    html.H3(folder["name"]),
                    html.Div(id={"type": "item-contents", "index": folder["_id"]}),
                    dbc.Button(
                        "Load",
                        id={"type": "load-item-button", "index": folder["_id"]},
                        outline=True,
                        size="sm",
                    ),
                ]
            )
            for folder in folders
        ]


@app.callback(
    Output({"type": "item-contents", "index": MATCH}, "children"),
    [Input({"type": "load-item-button", "index": MATCH}, "n_clicks")],
    [State({"type": "item-contents", "index": MATCH}, "id")],
)
def load_items(n, id):
    print("HELLO ITEM")
    if n is not None:
        response = requests.get(
            BASE_URL + "/item", params={"folderId": id["index"], "limit": 0}
        )
        items = response.json()
        return [
            html.Div(
                [
                    dcc.Checkbox(id={"type": "item-checkbox", "index": item["_id"]}),
                    html.Label(item["name"]),
                ]
            )
            for item in items
        ]


if __name__ == "__main__":
    app.run_server(debug=True)


# @app.callback(
#     Output("file_tree", "children"),
#     [Input("select_folder", "n_clicks")],
# )
# def add(n_clicks):
#     if n_clicks > 0:

#         children = DSAFileTree.build_tree(path, isRoot=True)
#         print(children)
#         return children


# app.layout = html.Div(
#     [
#         dbc.Alert(
#             "Either this URL is not a DSA, or the DSA cannot be reached (check CORS settings).",
#             id="error-alert",
#             color="danger",
#             dismissable=True,
#             is_open=False,
#         ),
#         dbc.Button("Log in", id="login-button"),
#         dbc.Modal(
#             [
#                 dbc.ModalHeader("DSA: " + BASE_URL),
#                 dbc.ModalBody(id="modal-body", children="Loading..."),
#                 dbc.ModalFooter(dbc.Button("Close", id="close", className="ml-auto")),
#             ],
#             id="login-modal",
#         ),
#         html.Div(id="dsa-content"),
#         dbc.Spinner(html.Div(id="loading")),
#     ]
# )


# @app.callback(
#     Output("login-modal", "is_open"),
#     [Input("login-button", "n_clicks"), Input("close", "n_clicks")],
#     [State("login-modal", "is_open")],
# )
# def toggle_modal(n1, n2, is_open):
#     if n1 or n2:
#         return not is_open
#     return is_open


# @app.callback(Output("dsa-content", "children"), [Input("login-modal", "is_open")])
# def update_dsa_content(is_open):
#     if not is_open:
#         response = requests.get(BASE_URL + "/collection", params={"limit": 0})
#         collections = response.json()
#         return [
#             html.Div(
#                 [
#                     html.H2(collection["name"]),
#                     html.Div(
#                         id={"type": "folder-contents", "index": collection["_id"]}
#                     ),
#                     dbc.Button(
#                         "Load",
#                         id={"type": "load-button", "index": collection["_id"]},
#                         outline=True,
#                         size="sm",
#                     ),
#                 ]
#             )
#             for collection in collections
#         ]


# @app.callback(
#     Output("selected-items", "children"),
#     [Input({"type": "item-checkbox", "index": ALL}, "value")],
# )
# def update_selected_items(values):
#     return "You have selected {} items".format(sum(values))


### The FileTree widget will start at a COLLECTION level.. that will be the root
### For now will not try and show all the collections..
