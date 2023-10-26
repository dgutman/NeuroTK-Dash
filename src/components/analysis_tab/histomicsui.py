from dash import html, callback, Input, Output, no_update
from ...utils.settings import gc

histomicsui = html.Div(
    html.Iframe(
        src="https://megabrain.neurology.emory.edu/histomics",
        style={"height": "100vh", "width": "100vw"},
        id="histomicsui-iframe",
    ),
)


@callback(
    Output("histomicsui-iframe", "src"),
    Input("project-itemSet-table", "selectedRows"),
    suppress_initial_call=True,
)
def update_histomicsui_image(row):
    if row is not None and row[0].get("_id"):
        item_id = row[0]["_id"]
        return f"https://megabrain.neurology.emory.edu/histomics?token={gc.token}#?image={item_id}"

    # Histomics?token=shdhjds#&imageid=737373

    return "https://megabrain.neurology.emory.edu/histomics"
