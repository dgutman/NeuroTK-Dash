import girder_client

import pandas as pd
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import dcc, no_update, html, callback, Input, Output, State
from ..utils.helpers import generate_generic_DataTable
from ..utils.api import get_all_containers, get_items_in_container
from ..utils.database import upsert_dsa_container_structure, get_dsa_container_structure

# from ..utils.api import gc


# NOTE can pull all cli functions using /cli then use the get xml api extension to get the details
# this will let you determine which inputs are float or sting for example, etc.


# NOTE: In the below, only the lowest folder returns annots, so this method is not performing recursive lookup

# lowest folder
# print(len([item for item in gc.get(f"annotation/folder/641c220d867536bb7a23be98?limit=0")]))

# highest folder
# print(len([item for item in gc.get(f"annotation/folder/641c220d867536bb7a23be96?limit=0")]))

# for item in list(gc.listResource("annotation"))[:5]:
#     print(item)

# print(len([item for item in gc.get(f"resource/641ba814867536bb7a225533/items?type=collection&limit=0")]))

# all_containers_datatable = html.Div(
#     [],
#     className="twelve columns item_datatable",
#     id="all_containers_datatable_div",
# )


all_containers_interface_div = html.Div([], id="all_containers_interface_div")
selected_container_items_datatable_div = html.Div([], id="selected_container_items_datatable_div")

guided_annots_panel = html.Div(
    [
        all_containers_interface_div,
        html.Br(),
        selected_container_items_datatable_div,
    ]
)

# NOTE: must be defined outside of update_container_cache because it is imported elsewhere
update_containers_button = dmc.Button(
    "Update DSA Structure Data",
    id="update_container_structure_button",
    n_clicks=0,
    variant="outline",
    compact=True,
    style={"width": "auto", "margin-left": "15px"},
)

# NOTE must be defined up here because the loading animation requires the original button returned when the task
# has completed, so it's better to define the button as a reusable component
transfer_list_update_button = dmc.Button(
    "Update Available with Content of Selected",
    id="transfer_list_update_button",
    n_clicks=0,
    variant="outline",
    compact=True,
)

get_items_from_transfer_list_button = dmc.Button(
    "Get Details of Items in Selected",
    id="get_items_from_transfer_list_button",
    n_clicks=0,
    variant="outline",
    compact=True,
    style={"margin-left": "50px"},  # not perfect but better
)


@callback(
    [Output("loading_container_structure", "children")],
    [Input("update_container_structure_button", "n_clicks")],
    prevent_initial_call=True,
)
def update_container_cache(n_clicks, debug=False):
    if n_clicks:
        container_structure = get_all_containers()

        status = upsert_dsa_container_structure(container_structure)

        if debug:
            print(status)

    return [update_containers_button]


def generate_container_transfer_list(container_structure):
    # converting from BSON to string
    container_structure["_id"] = container_structure["_id"].astype(str)

    # print(container_structure.columns)

    filt = container_structure["item_type"] == "collection"
    collection_data = container_structure.loc[filt, ["_id", "item_name", "parent_name"]].copy()

    collection_data.rename(columns={"_id": "value", "item_name": "label", "parent_name": "group"}, inplace=True)
    collection_data = [collection_data.to_dict(orient="records"), []]

    collection_transfer_list = dmc.TransferList(
        titles=["Available Containers(s)", "Selected Containers"],
        searchPlaceholder=["Search item to add...", "Search item to remove..."],
        id="collection_transfer_list",
        value=collection_data,
        showTransferAll=True,
        transferAllMatchingFilter=True,
    )

    return collection_transfer_list


@callback(
    [
        Output("container_store", "data"),
        Output("all_containers_interface_div", "children"),
    ],
    [Input("guided_annots_accordion", "n_clicks")],
)
def store_all_container_data(n_clicks, debug=False):
    container_structure = pd.DataFrame(get_dsa_container_structure())

    if debug:
        print(container_structure)

    collection_transfer_list = generate_container_transfer_list(container_structure)

    main_children = [
        dbc.Row([collection_transfer_list], id="transfer_list_row"),
        html.Br(),
        dbc.Row(id="transfer_list_buttons"),
    ]

    return container_structure.to_dict(orient="records"), main_children


@callback(
    [Output("transfer_list_buttons", "children")],
    [Input("collection_transfer_list", "value")],
    prevent_initial_call=True,
)
def return_transfer_list_buttons(n_clicks):
    buttons = html.Div(
        dbc.Row(
            [
                dbc.Col(
                    dcc.Loading(
                        id="loading_updated_transfer_list",
                        type="default",
                        children=[
                            transfer_list_update_button,
                        ],
                    ),
                    width="auto",
                ),
                dbc.Col(
                    dcc.Loading(
                        id="loading_selected_items_from_transfer_list",
                        type="default",
                        children=[
                            get_items_from_transfer_list_button,
                        ],
                    ),
                    width="auto",
                ),
            ]
        )
    )
    return [buttons]


@callback(
    [
        Output("transfer_list_row", "children"),
        Output("loading_updated_transfer_list", "children"),
    ],
    [
        Input("transfer_list_update_button", "n_clicks"),
        State("collection_transfer_list", "value"),
        State("container_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_transfer_list(n_clicks, current_state, cached_containers):
    if n_clicks:
        selected = current_state[1]
        df = pd.DataFrame(cached_containers)

        filt = df["parent_name"].isin([val["label"] for val in selected])
        available = df.loc[filt, ["_id", "item_name", "parent_name"]].copy()

        filt = available["_id"].isin([val["value"] for val in selected])
        available = available[~filt]

        available.rename(columns={"_id": "value", "item_name": "label", "parent_name": "group"}, inplace=True)
        available = available.to_dict(orient="records")

        selected.extend(available)
        updated = dmc.TransferList(
            titles=["Available Containers(s)", "Selected Containers"],
            searchPlaceholder=["Search item to add...", "Search item to remove..."],
            id="collection_transfer_list",
            value=[selected, []],
            showTransferAll=True,
            transferAllMatchingFilter=True,
        )

        return [updated], [get_items_from_transfer_list_button]

    return no_update


@callback(
    [
        Output("selected_container_items_datatable_div", "children"),
        Output("loading_selected_items_from_transfer_list", "children"),
    ],
    [
        Input("get_items_from_transfer_list_button", "n_clicks"),
        State("collection_transfer_list", "value"),
    ],
    prevent_initial_call=True,
)
def get_transfer_list_item_details(n_clicks, current_state):
    if n_clicks:
        selected = pd.DataFrame(current_state[1])

        filt = selected["label"].isin(selected["group"])
        selected = selected[~filt]

        filt = selected["group"] == "Collection"
        collections = selected[filt].copy()
        folders = selected[~filt].copy()

        items = [
            pd.json_normalize(get_items_in_container(collection_id, container_type="collection"), sep="_")
            for collection_id in collections["value"].tolist()
        ]
        items.extend(
            [pd.json_normalize(get_items_in_container(folder_id), sep="_") for folder_id in folders["value"].tolist()]
        )

        df = pd.concat(items)

        # print(df.head())
        # print(df.columns)

        datatable = generate_generic_DataTable(df, "selected_container_items_datatable")

        return [datatable], [get_items_from_transfer_list_button]

    return no_update
