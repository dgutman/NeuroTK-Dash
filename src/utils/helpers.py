from dash import html
import dash_ag_grid as dag


def generate_generic_DataTable(df, id_val, col_defs={}, exportable=False):
    col_defs = [{"field": col} for col in df.columns] if not col_defs else col_defs

    dsa_datatable = html.Div(
        [
            dag.AgGrid(
                id=id_val,
                enableEnterpriseModules=True,
                className="ag-theme-alpine-dark",
                defaultColDef={
                    "filter": "agSetColumnFilter",
                    "editable": True,
                    "flex": 1,
                    "filterParams": {"debounceMs": 2500},
                    "floatingFilter": True,
                },
                columnDefs=col_defs,
                rowData=df.to_dict("records"),
                dashGridOptions={"pagination": True, "paginationAutoPageSize": True},
                columnSize="sizeToFit",
                csvExportParams={
                    "fileName": f"{id_val.replace('-', '_')}.csv",
                }
                if exportable
                else {},
                style={'height': '75vh'}
            ),
        ]
    )

    return dsa_datatable
