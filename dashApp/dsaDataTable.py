from dash import Dash, html, dcc, callback, Output, Input, dash_table


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
        ),
        html.Div(id='datatable-interactivity-container')
    ])

    return dsa_datatable
