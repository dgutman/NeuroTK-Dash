### This module creates a layout to view the annotation data from the DSA that is cached locally in a mongo table
## We can add all the filters and fun stuff here related to showing annotations, as well as overlaying annotations on images
### For now we will simply display a datatable... but cooler stuff.. coming soon!
from dash import html, callback, Output, Input
from ..utils.api import getAllItemAnnotations
from ..utils.database import insertAnnotationData, getAnnotationData_fromDB
from ..utils.helpers import generate_generic_DataTable
import pandas as pd
import json

update_annotation_button = html.Button(
    "Update Annotation DataSet",
    id="update-annotations-btn",
    n_clicks=0,
)

projectName = "evanPPC"
debug = False


def clean_groups(groups):
    return {f"group_{count}": val for count, val in enumerate(groups, 1) if val is not None}


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
    if (desc := record["annotation"].get("description", False)) and desc.startswith("Used params"):
        record["annotation"]["description"] = None

    if record["groups"]:
        record.update(clean_groups(record["groups"]))

    record.pop("groups")

    return record


@callback(
    Output("update-annotations-btn", "n_clicks"),
    Input("update-annotations-btn", "n_clicks"),
)
def update_all_annots_cache(n_clicks):
    ## This should update the annotations if clicked, otherwise, just get the current data in the database..
    if n_clicks:
        annotationItemSet = getAllItemAnnotations()

        annotationItemSet = [
            (parse_annot(item) if item["annotation"]["name"] != "Positive Pixel Count" else parse_PPC(item))
            for item in annotationItemSet
        ]

        ### Now update the database...
        status = insertAnnotationData(annotationItemSet, projectName)
        if debug:
            print(status)

    return 0


@callback(
    [Output("all-annotations-datatable-div", "children")],
    [Input("all_annots_accordion", "n_clicks")],
)
def updateAnnotationDataFromGirder(n_clicks):
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

    return None
