# Utility functions.
from girder_client import GirderClient
from typing import List

from dash import html
import dash_ag_grid as dag

# TODO: eventually split this into things which interface with the DSA API and things which generate components for the app


def get_projects(gc: GirderClient, fld_id: str) -> List[dict]:
    """Get a list of NeuroTK folders for the user.

    Args:
        gc: Girder client.
        fld_id: DSA id of NeuroTK Projects folder.

    Returns:
        List of project metadata.

    """
    # Loop through public and then private folders.
    projects = []

    for fld in gc.listFolder(fld_id):
        for user in gc.listFolder(fld["_id"]):
            for project in gc.listFolder(user["_id"]):
                project["key"] = f"{user['name']}/{project['name']}"
                projects.append(project)

    return projects


def generate_generic_DataTable(df, id_val, default_col_def={"resizable": True}, col_defs={}, exportable=False):
    col_defs = [{"field": col} for col in df.columns] if not col_defs else col_defs
    dsa_datatable = html.Div(
        [
            dag.AgGrid(
                id=id_val,
                enableEnterpriseModules=True,
                className="ag-theme-alpine-dark",
                defaultColDef=default_col_def,
                columnDefs=col_defs,
                rowData=df.to_dict("records"),
                dashGridOptions={"pagination": True},
                columnSize="sizeToFit",
                csvExportParams={
                    "fileName": f"{id_val.replace('-', '_')}.csv",
                }
                if exportable
                else {},
            ),
        ]
    )

    return dsa_datatable
