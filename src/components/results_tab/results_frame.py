"""
This will contain various functionality related to viewing consolidated 
results from a given analysis.
"""
import dash
from dash import html, Input, Output, State, dcc, callback

from .results_panels import ppc_results_panel
from ...utils.settings import dbConn


results_frame = html.Div(
    [
        # Stores annotation documents related to selected task.
        dcc.Store(id="results-store", data=[]),
        html.Div(id="results-graphs-and-tables", style={"height": "100vh"}),
    ]
)


@callback(
    Output("results-store", "data"),
    Input("filteredItem_store", "data"),
    [State("tasks-dropdown", "value"), State("task-store", "data")],
)
def update_results_store(items, selected_task, task_store):
    if selected_task and len(items):
        # Grab information for the task.
        if selected_task in task_store:
            task_item = task_store[selected_task]

            # Get a list of image IDs currently loaded in the datatable.
            items = {item["_id"]: item for item in items}

            task_meta = task_item.get("meta", {})

            if task_meta.get("cli") == "PositivePixelCount":
                docname = "Positive Pixel Count"
            elif task_meta.get("params", {}).get("docname"):
                docname = task_meta["params"]["docname"]
            else:
                print(
                    f"Task {selected_task} is not currently supported for report panel."
                )
                return dash.no_update

            # Look for annotation documents in mongo that match this task and image list.
            annotation_docs = dbConn["annotationData"].find(
                {
                    "annotation.name": docname,
                    "itemId": {"$in": list(items.keys())},
                },
                {
                    "itemId": 1,
                    "annotation.attributes.stats": 1,
                    "annotation.attributes.params": 1,
                },
            )

            task_docs = []
            task_params = task_meta.get("params", {})

            if "region" in task_params:
                del task_params["region"]

            annotation_docs = list(annotation_docs)
            for doc in annotation_docs:
                if doc.get("annotation", {}).get("attributes", {}).get("stats"):
                    doc_params = doc["annotation"]["attributes"].get("params", {})

                    # Check the param list.
                    doc_flag = True

                    for k, v in task_params.items():
                        if doc_params[k] != v:
                            doc_flag = False
                            break

                    if doc_flag:
                        # This may be just temporary and filters out annotation docs not run on annotated regions.
                        if len(doc_params["region"]) < 10:
                            continue

                        # Reformat the dictionary to make more sense.
                        # doc.update(doc["annotation"]["attributes"]["stats"])
                        # del doc["annotation"]["attributes"]["stats"]
                        # doc.update(doc["annotation"]["attributes"]["params"])
                        # del doc["annotation"]["attributes"]["params"]

                        doc.update(items[doc["itemId"]])
                        task_docs.append(doc)

            return task_docs
        else:
            print(
                "Could not find the selected task in the task store, there must be some bug!"
            )

        return []
    else:
        return []


@callback(
    Output("results-graphs-and-tables", "children"),
    Input("results-store", "data"),
    [State("tasks-dropdown", "value"), State("task-store", "data")],
    prevent_initial_call=True,
)
def generate_results(data, selected_task, task_store):
    # Get the type of task selected to load the appropriate report panel
    task_item = task_store[selected_task]

    cli = task_item.get("meta", {}).get("cli")

    if cli == "PositivePixelCount":
        return [ppc_results_panel]
    else:
        print(f"No results panel yet supported for {cli} CLI task.")
        return html.Div()
