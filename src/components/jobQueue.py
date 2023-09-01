from dash import html, dcc, callback, Input, Output, State, no_update
import dash_ag_grid
from ..utils.database import mc
import dash_bootstrap_components as dbc
import aiohttp
from ..utils.api import gc
import dash, json

jobQueue_frame = html.Div(
    [
        dbc.Button("Check Job Status", id="check-job-status-button", color="primary"),
        dbc.Button(
            "Refresh Job Status", id="refresh-job-status-button", color="warning"
        ),
        dash_ag_grid.AgGrid(
            id="my-grid",
            columnDefs=[
                {"headerName": "Job ID", "field": "_id"},
                {"headerName": "Title", "field": "title"},
                {"headerName": "Status", "field": "status"},
                {"headerName": "Created", "field": "created"},
            ],
            defaultColDef={"resizable": True, "sortable": True, "filter": True},
            dashGridOptions={"pagination": True, "paginationAutoPageSize": True},
            rowData=[],
            columnSize="sizeToFit",
        ),
        dcc.Interval(
            id="interval-update",
            interval=5 * 1000,  # Update every 5 seconds
            n_intervals=0,
        ),
        dbc.Toast(
            "Refresh complete",
            id="refresh-toast",
            header="Notification",
            is_open=False,
            dismissable=True,
            icon="info",
            duration=4000,
        ),
        html.Div(id="refreshStatusDiv"),
    ]
)


@callback(Output("my-grid", "rowData"), Input("interval-update", "n_intervals"))
def update_table(n):
    # Fetch data from MongoDB
    collection = mc["dsaJobQueue"]
    job_data = list(
        collection.find({}, {"_id": 1, "title": 1, "status": 1, "created": 1})
    )
    return job_data


# Async Callbacks
@callback(
    Output("refreshStatusDiv", "children"),
    Input("refresh-job-status-button", "n_clicks"),
)
def refresh_jobs(n_clicks):
    if n_clicks is None:
        return dash.no_update

    collection = mc["dsaJobQueue"]
    # Find jobs with status 0
    jobs = collection.find({"status": 0})

    ## TO DO.. maybe enumerate this or something?
    jobsScanned = 0
    for job in jobs:
        job_id = job["_id"]
        currentJobInfo = gc.get(f"job/{job_id}")
        newStatus = currentJobInfo["status"]
        # Update MongoDB
        print(json.dumps(newStatus, indent=2))
        collection.update_one({"_id": job_id}, {"$set": {"status": newStatus}})
        jobsScanned += 1
    return [html.Div(jobsScanned, "were scanned")]
