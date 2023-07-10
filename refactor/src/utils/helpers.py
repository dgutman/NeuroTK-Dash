import pandas as pd
from dash import html, dash_table


def getSampleDataset(itemSet_json):
    df = pd.json_normalize(itemSet_json, sep=".")
    selected_columns = ["_id", "name", "meta.npSchema.blockID",
                        "meta.npSchema.caseID", "meta.npSchema.regionName", "meta.npSchema.stainID"]
    df = df[selected_columns]
    column_mapping = {
        "meta.npSchema.blockID": "blockID",
        "meta.npSchema.caseID": "caseID",
        "meta.npSchema.regionName": "regionName",
        "meta.npSchema.stainID": "stainID"
    }
    # Rename the columns using the dictionary mapping
    df = df.rename(columns=column_mapping)
    return df


def generate_dsaAnnotationsTable(df):

    dsa_AnnotationDatatable = html.Div([
        dash_table.DataTable(
            id='annotation-datatable',
            columns=[
                {"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=6,
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': '500px',  # Adjust as needed
                'maxWidth': '100%',  # Adjust as needed
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_cell={
                'textAlign': 'left',
                'minWidth': '120px',  # Adjust as needed
                'maxWidth': '180px',  # Adjust as needed
                'whiteSpace': 'no-wrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
            }
        ),

    ])
    return dsa_AnnotationDatatable
    


def generate_dsaDataTable(df):
    dsa_datatable = html.Div([
        dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=6,
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': '500px',  # Adjust as needed
                'maxWidth': '100%',  # Adjust as needed
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_cell={
                'textAlign': 'left',
                'minWidth': '120px',  # Adjust as needed
                'maxWidth': '180px',  # Adjust as needed
                'whiteSpace': 'no-wrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
            }
        ),
        # html.Div(id='datatable-interactivity-container')
    ])

    return dsa_datatable
