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
        self.id = id

    def getResourcePathId(self, resourcePath):
        rp = gc.get("/resource/lookup?path=%s" % resourcePath)
        if rp:
            return rp["_id"]
        else:
            return None

    def render(self) -> dmc.Accordion:
        return dmc.AccordionMultiple(
            self.build_tree(
                self.resourcePath, id=self.id, isRoot=True, parentFolderType="folder"
            ),
            id=self.id,
        )

    def flatten(self, l):
        return [item for sublist in l for item in sublist]

    def make_file(self, file_name):
        return dmc.Text(
            [DashIconify(icon="akar-icons:file"), " ", file_name],
            style={"paddingTop": "5px"},
        )

    def make_folder(self, folder_name):
        return [DashIconify(icon="akar-icons:folder"), " ", folder_name]

    def list_folder(self, path, parentFolderType="folder"):
        ### list a folder from the DSA
        print("Listing folder", path)
        pathId = self.getResourcePathId(path)

        fldrList = [x["name"] for x in gc.listFolder(pathId, parentFolderType)]
        print(list(fldrList))
        return fldrList

    def build_tree(self, path, id, isRoot=False, parentFolderType="folder"):
        ## Main modification is here.. Will use the girder Path lookup functionality
        ## So this is easier to follow than if using IDs.. can also add a class
        ## to cache the folders .. although not sure if that is particularly useful
        print("Processing path: %s" % path)
        d = []
        if self.getResourcePathId(path):
            children = [
                self.build_tree(os.path.join(path, x), path)
                for x in self.list_folder(path, parentFolderType)
            ]
            print(children)
            if isRoot:
                return self.flatten(children)
            item = dmc.AccordionItem(
                [
                    dmc.AccordionControl(self.make_folder(os.path.basename(path))),
                    dmc.AccordionPanel(children=self.flatten(children)),
                ],
                value=path,
            )
            d.append(item)
        else:
            d.append(self.make_file(os.path.basename(path)))
            # item = dmc.AccordionItem(
            #        [     dmc.AccordionControl(self.make_folder(os.path.basename(path)),

            #         ],value=path)
            #     )
        #     else:
        #         d.append(
        #             dmc.Accordion(
        #                 children=[
        #                     dmc.AccordionItem(
        #                         children=children,
        #                         value=self.make_folder(os.path.basename(path)),
        #                     )
        #                 ],
        #                 value=os.path.basename(path),
        #                 id=path,  ### Make the id of this resource the resourcePath
        #             )
        #         )
        # else:
        #     d.append(self.make_file(os.path.basename(path)))
        return d


# Usage
## I am using the DSA resource path it's easier to follow

dsaResourcePath = "/collection/NeuroPathDemoImages/2020/E20-106"  # Any filepath here

fileTreeLayout = DSAFileTree(dsaResourcePath, gc, "file_tree_root").render()
print(fileTreeLayout)

app.layout = dbc.Row(
    [
        html.Div("Stuff goes here too"),
        fileTreeLayout,
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True)


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
#     Output({"type": "folder-contents", "index": MATCH}, "children"),
#     [Input({"type": "load-button", "index": MATCH}, "n_clicks")],
#     [State({"type": "folder-contents", "index": MATCH}, "id")],
# )
# def load_collection(n, id):
#     if n is not None:
#         response = requests.get(
#             BASE_URL + "/folder",
#             params={"parentType": "collection", "parentId": id["index"], "limit": 0},
#         )
#         folders = response.json()
#         return [
#             html.Div(
#                 [
#                     html.H3(folder["name"]),
#                     html.Div(id={"type": "item-contents", "index": folder["_id"]}),
#                     dbc.Button(
#                         "Load",
#                         id={"type": "load-item-button", "index": folder["_id"]},
#                         outline=True,
#                         size="sm",
#                     ),
#                 ]
#             )
#             for folder in folders
#         ]


# @app.callback(
#     Output({"type": "item-contents", "index": MATCH}, "children"),
#     [Input({"type": "load-item-button", "index": MATCH}, "n_clicks")],
#     [State({"type": "item-contents", "index": MATCH}, "id")],
# )
# def load_items(n, id):
#     if n is not None:
#         response = requests.get(
#             BASE_URL + "/item", params={"folderId": id["index"], "limit": 0}
#         )
#         items = response.json()
#         return [
#             html.Div(
#                 [
#                     dcc.Checkbox(id={"type": "item-checkbox", "index": item["_id"]}),
#                     html.Label(item["name"]),
#                 ]
#             )
#             for item in items
#         ]


# @app.callback(
#     Output("selected-items", "children"),
#     [Input({"type": "item-checkbox", "index": ALL}, "value")],
# )
# def update_selected_items(values):
#     return "You have selected {} items".format(sum(values))

# app.layout = html.Div(
#     [
#         html.Details(
#             [
#                 html.Summary(
#                     html.A(id="outer-link", children=["Outer Link"]),
#                 ),
#                 html.Div(
#                     [
#                         html.Details(
#                             html.Summary(
#                                 html.A(id="inner-link", children=["Inner Link"])
#                             )
#                         )
#                     ],
#                     style={"text-indent": "2em"},
#                 ),
#             ]
#         ),
#         html.Div(id="outer-count"),
#         html.Div(id="inner-count"),
#         html.Div(id="last-clicked"),
#     ]
# )


# @app.callback(
#     [
#         Output("outer-count", "children"),
#         Output("inner-count", "children"),
#         Output("last-clicked", "children"),
#     ],
#     [
#         Input("outer-link", "n_clicks"),
#         Input("outer-link", "n_clicks_timestamp"),
#         Input("inner-link", "n_clicks"),
#         Input("inner-link", "n_clicks_timestamp"),
#     ],
# )
# def divclick(outer_link_clicks, outer_link_time, inner_link_clicks, inner_link_time):
#     if outer_link_time is None:
#         outer_link_time = 0
#     if inner_link_time is None:
#         inner_link_time = 0

#     timestamps = {
#         "None": 1,
#         "Outer Link": outer_link_time,
#         "Inner Link": inner_link_time,
#     }

#     last_clicked = max(timestamps, key=timestamps.get)

#     return (
#         "Outer link clicks: " + str(outer_link_clicks),
#         "Inner link clicks: " + str(inner_link_clicks),
#         "Last clicked: " + last_clicked,
#     )


### The FileTree widget will start at a COLLECTION level.. that will be the root
### For now will not try and show all the collections..
