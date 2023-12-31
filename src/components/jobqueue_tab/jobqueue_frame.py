from dash import html, dcc, callback, Input, Output, State, dcc
import dash_ag_grid
import dash_bootstrap_components as dbc
import dash, json
import pandas as pd
import plotly.express as px

from ...utils.database import mc
from ...utils.api import gc
from ...utils.settings import dbConn

jobStatusQueue_map = {4: "fail", 3: "sucess", 2: "running", 1: "queued", 0: "inactive"}
# status codes -- 4: fail, 3: success, 0: inactive, 1/2: queued/running


## TO DO: Probably want to add something that looks only within last 24 hours or some sort of timeframe

jobQueue_button_controls = html.Div(
    [
        dcc.Store("jobInfo_store"),
        html.Button(
            "Check Job Status",
            id="check-job-status-button",
            className="mr-2 btn btn-primary",
        ),
        html.Button(
            "Refresh Job Status",
            id="refresh-job-status-button",
            className="mr-2 btn btn-warning",
        ),
    ],
    className="d-grid gap-2 d-md-flex justify-content-md-begin",
)


jobqueue_frame = html.Div(
    dbc.Container(
        [
            dbc.Row(jobQueue_button_controls),
            dbc.Row(
                [
                    dbc.Col(
                        dash_ag_grid.AgGrid(
                            id="jobData_table",
                            columnDefs=[
                                {"headerName": "Job ID", "field": "_id"},
                                {"headerName": "Title", "field": "title"},
                                {"headerName": "Status Code", "field": "status"},
                                {"headerName": "Status", "field": "statusText"},
                                {"headerName": "Created", "field": "created"},
                            ],
                            defaultColDef={
                                "resizable": True,
                                "sortable": True,
                                "filter": True,
                            },
                            dashGridOptions={
                                "pagination": True,
                                "paginationAutoPageSize": True,
                            },
                            rowData=[],
                            columnSize="sizeToFit",
                        ),
                        width=9,
                    ),
                    dbc.Col(dcc.Graph("job-status-pieChart"), width=3),
                ]
            ),
            dbc.Row([html.Div(id="refreshStatusDiv")]),
        ]
    )
)


@callback(Output("job-status-pieChart", "figure"), Input("jobInfo_store", "data"))
def createJobStatusPieChart(data):
    if data:
        df = pd.DataFrame(data)

        # Count the frequency of each unique 'statusCode'
        status_count = df["statusText"].value_counts().reset_index()
        status_count.columns = ["status", "count"]

        # Generate the pie chart
        fig = px.pie(
            status_count,
            values="count",
            names="status",
            title="Distribution of Status Codes",
        )
        return fig
    else:
        return px.pie()


@callback(Output("jobData_table", "rowData"), Input("jobInfo_store", "data"))
def update_jobDataTable(data):
    ## On iupdates to the jobinfo store, update the jobdata table
    return data


@callback(Output("jobInfo_store", "data"), Input("check-job-status-button", "n_clicks"))
def getJobInfoFromMongo(n_clicks):
    # Fetch data from MongoDB
    collection = mc["dsaJobQueue"]
    job_data = list(
        collection.find({}, {"_id": 1, "title": 1, "status": 1, "created": 1})
    )

    if job_data:
        df = pd.DataFrame(job_data)
        df["statusText"] = df.status.map(jobStatusQueue_map)
        return df.to_dict("records")
    else:
        return []


# Async Callback to be implemented
@callback(
    Output("refreshStatusDiv", "children"),
    Input("refresh-job-status-button", "n_clicks"),
)
def refresh_jobs(n_clicks):
    if n_clicks is None:
        return dash.no_update

    collection = dbConn["dsaJobQueue"]

    # Find jobs with status 0 == inactive
    jobs = collection.find({"status": {"$in": [0, 1, 2]}})

    ## TO DO.. maybe enumerate this or something?
    jobsScanned = 0
    for job in jobs:
        job_id = job["_id"]
        currentJobInfo = gc.get(f"job/{job_id}")
        newStatus = currentJobInfo["status"]

        # Update the mongo database.
        collection.update_one({"_id": job_id}, {"$set": {"status": newStatus}})
        jobsScanned += 1

    return [html.Div(jobsScanned, "were scanned")]
