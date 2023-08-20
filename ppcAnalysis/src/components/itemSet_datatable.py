"""Item Set Datatable keeps track of the items from the DSA"""
from dash import html, callback, dcc, Input, Output, State
import dash_mantine_components as dmc
from ..utils.helpers import getItemDataset, generate_main_DataTable
from ..utils.database import get_all_records_df
import pandas as pd

## Add a button to refresh the annotations, this will pull or refresh the database

update_items_button = dmc.Button(
    "Update Item Data",
    id="update-items-button",
    n_clicks=0,
    variant="outline",
    compact=True,
    style={"width": "auto"},
)


itemSet_store = dcc.Store(id='itemSet_store')

## T/his contains an update button, the itemStore storage element, and a div to actually hold the data table
main_item_datatable = html.Div([update_items_button,itemSet_store,html.Div( id="item-datatable-div")], className="twelve columns item_datatable")

# This callback should only populate the main item datatable
@callback(
    [Output("item-datatable-div", "children")],
    [Input("itemSet_store", "data")],
)
def populate_main_datatable(data):
    if data is None:
        samples_dataset = get_all_records_df()
    else:
        samples_dataset = pd.DataFrame(data)

    if samples_dataset.empty:
        table = None
    else:
        samples_dataset.rename(columns={"_id": "Item ID"}, inplace=True)
        table = generate_main_DataTable(samples_dataset, id_val="dag-main-table")

    return [table]
