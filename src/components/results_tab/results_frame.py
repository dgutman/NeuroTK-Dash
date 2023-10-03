"""This will contain various functionality related to viewing consolidated results from a given analysis.. starting with PPC"""
from dash import html, Input, Output, State, dcc, ctx, callback
import dash_ag_grid as dag
from ...utils.settings import dbConn
import dash_bootstrap_components as dbc
from ...utils.helpers import generate_generic_DataTable
import pandas as pd
import json
from pprint import pprint

resultSelectOptions = ["There", "Are", "None"]

results_frame = html.Div(
    [
        dcc.Store(id="ppcResults_store", data=[]),
        dbc.Select(
            id="selectPPCResultSet",
            options=resultSelectOptions,
            value=resultSelectOptions[0],
            style={"maxWidth": 200},
        ),
        html.Div(id="ppcResults_datatable"),
    ]
)


@callback(Output("ppcResults_store", "data"), Input("selectPPCResultSet", "value"))
def populatePPCResultStore(selectValue):
    """The select value is just a place holder... currently it doesn't do anything but eventually we will want
    to pull results based on the specific selected task and data set... again.. PLACE HOLDER!!
    """
    ppcDocs = dbConn["annotationData"].find(
        {"annotation.name": "Positive Pixel Count"}, {"annotation.description": 1}
    )

    fixedPPC = []

    for p in ppcDocs:
        p = parse_PPC(p)
        # pprint(p)
        fixedPPC.append(p)

    return fixedPPC


def clean_groups(groups):
    return {
        f"group_{count}": val for count, val in enumerate(groups, 1) if val is not None
    }


def parse_PPC(record):
    # record["created"] = record["created"].split("T")[0]

    try:
        description = json.loads(
            record["annotation"]["description"]
            .replace("Used params: ", "{'params':")
            .replace("\nResults:", ',"Results":')
            .replace("'", '"')
            .replace("None", "null")
            + "}"
        )
    except:
        print("Something wrong with document", record)
        return record

    record["test"] = description

    # if record["groups"] is not None:
    #     record.update(clean_groups(record["groups"]))

    # record.pop("groups")

    return record


@callback(Output("ppcResults_datatable", "children"), Input("ppcResults_store", "data"))
def generatePPCResultsTable(data):
    df = pd.json_normalize(data)

    ppcResults_datatable = generate_generic_DataTable(df, "ppc_dt")
    # print(ppcResults_datatable)
    return ppcResults_datatable


# ppcResults_datatable

## Now return a datatable..


## First create a store to hold the current PPC results...
