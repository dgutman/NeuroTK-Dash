from dash import html, Output, Input, State, callback
import dash_mantine_components as dmc
import json
from ..utils.api import getAllItemAnnotations
from ..utils.database import insertAnnotationData, getAnnotationData_fromDB
from ..utils.helpers import generate_generic_DataTable
import pandas as pd

debug = False


def clean_groups(groups):
    return {
        f"group_{count}": val for count, val in enumerate(groups, 1) if val is not None
    }


update_annotation_button = dmc.Button(
    "Update Annotation DataSet",
    id="update-annotations-btn",
    n_clicks=0,
    variant="outline",
    compact=True,
    style={"width": "auto", "margin-left": "15px"},
)


### TO DO  Change this to just load the data into a datastore instead of from the database
@callback(
    [Output("all-annotations-datatable-div", "children")],
    [Input("update-annotations-btn", "n_clicks")],
    [State("projects-select", "value")],
)
def updateAnnotationDataFromGirder(n_clicks, projectName):
    ### Pull the annotation Data from girder and load it into the mongo database, we will then return a table as well...
    annotationItemData = getAnnotationData_fromDB(projectName=projectName)

    if annotationItemData:
        df = pd.json_normalize(annotationItemData, sep="_")

        keep_cols = [
            "_id",
            "itemId",
            "created",
            "projectName",
            "annotation_name",
            "annotation_description",
            "annotation_attributes_stats_RatioStrongToPixels",
        ]

        keep_cols.extend([col for col in df.columns if col.startswith("group")])
        df = df[keep_cols]

        mapped_vals = {
            "itemId": "item ID",
            "_id": "annotation ID",
            "annotation_name": "Annotation Name",
            "annotation_description": "Annotation Description",
            "annotation_attributes_stats_RatioStrongToPixels": "Percent Strong Positive",
        }
        df.rename(columns=mapped_vals, inplace=True)

        df.dropna(how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)

        return [generate_generic_DataTable(df, id_val="dag_all_annotations_table")]

    return [None]


annotation_datatable = html.Div(
    [update_annotation_button, html.Div(id="all-annotations-datatable-div")]
)


@callback(
    [Output("loading_annots", "children")],
    [Input("update-annotations-btn", "n_clicks")],
    prevent_intial_call=True,
)
def update_all_annots_cache(n_clicks):
    ## This should update the annotations if clicked, otherwise, just get the current data in the database..
    if n_clicks:
        annotationItemSet = getAllItemAnnotations()

        annotationItemSet = [
            (
                parse_annot(item)
                if item["annotation"]["name"] != "Positive Pixel Count"
                else parse_PPC(item)
            )
            for item in annotationItemSet
        ]

        ### Now update the database...
        status = insertAnnotationData(annotationItemSet, projectName)
        if debug:
            print(status)

    return [update_annotation_button]


def parse_annot(record):
    record["created"] = record["created"].split("T")[0]

    # NOTE: this is just placeholder because there are some that have Used params but which have no relevant data
    # this will likely change as we do more/different interogations of the data/these images, so this will
    # likely need to be updated in the near future
    if (desc := record["annotation"].get("description", False)) and desc.startswith(
        "Used params"
    ):
        record["annotation"]["description"] = None

    if record["groups"]:
        record.update(clean_groups(record["groups"]))

    record.pop("groups")

    return record


def parse_PPC(record):
    record["created"] = record["created"].split("T")[0]

    description = json.loads(
        record["annotation"]["description"]
        .replace("Used params: ", "{'params':")
        .replace("\nResults:", ',"Results":')
        .replace("'", '"')
        .replace("None", "null")
        + "}"
    )

    record["annotation"]["description"] = description

    if record["groups"] is not None:
        record.update(clean_groups(record["groups"]))

    record.pop("groups")

    return record


def parse_annot(record):
    record["created"] = record["created"].split("T")[0]

    # NOTE: this is just placeholder because there are some that have Used params but which have no relevant data
    # this will likely change as we do more/different interogations of the data/these images, so this will
    # likely need to be updated in the near future
    if (desc := record["annotation"].get("description", False)) and desc.startswith(
        "Used params"
    ):
        record["annotation"]["description"] = None

    if record["groups"]:
        record.update(clean_groups(record["groups"]))

    record.pop("groups")

    return record
