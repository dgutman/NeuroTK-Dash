import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH
import os
from flask import Flask
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc

# server = Flask(__name__)

# app = dash.Dash(server=server)


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
    ],
)

root_folder = "/home/dagutman/devel"


## There's folder  and then folder-close and folder-open


def folder_div(folder_path, level=0):
    return html.Div(
        [
            dmc.Button(
                os.path.basename(folder_path),
                # rightIcon=DashIconify(icon="akar-icons:folder-open", width=20),
                leftIcon=DashIconify(
                    icon="material-symbols:folder-close"
                    if level % 2 == 0
                    else "material-symbols:folder-open"
                ),
                id={"type": "folder", "path": folder_path},
                n_clicks=0,
                variant="outline",
                style={"text-align": "left", "margin-left": f"{20*level}px"},
            ),
            html.Div(
                id={"type": "subfolders", "path": folder_path},
                style={"margin-left": f"{20*(level+1)}px"},
            ),
        ]
    )


app.layout = html.Div(
    [
        dcc.Markdown("## Folder Tree"),
        html.Div(
            folder_div(root_folder),
            style={
                "max-height": "600px",
                "overflow": "auto",
                "border": "1px solid #ddd",  # Optional: adds a border around the div
                "padding": "10px",  # Optional: adds some space around the content
            },
        ),
        html.Div(id={"type": "selected-folder", "path": root_folder}),
    ]
)


@app.callback(
    Output({"type": "selected-folder", "path": MATCH}, "children"),
    [Input({"type": "folder", "path": MATCH}, "n_clicks")],
    [State({"type": "folder", "path": MATCH}, "id")],
)
def display_selected_folder(n_clicks, folder_id):
    print(folder_id)
    if n_clicks > 0:
        return f"You selected folder: {folder_id['path']}"
    return "No folder selected"


@app.callback(
    Output({"type": "subfolders", "path": MATCH}, "children"),
    [Input({"type": "folder", "path": MATCH}, "n_clicks")],
    [State({"type": "folder", "path": MATCH}, "id")],
)
def toggle_folder(n_clicks, folder_id):
    level = folder_id["path"].count(os.sep) - root_folder.count(os.sep)
    if n_clicks % 2 == 1:  # folder was expanded
        try:
            subfolders = os.listdir(folder_id["path"])
            if subfolders:  # if there are subfolders, update the folder icon to "open"
                folder_id["icon"] = "material-symbols:folder-open"
            else:  # if there are no subfolders, keep the folder icon as "closed"
                folder_id["icon"] = "material-symbols:folder-close"
            return [
                folder_div(os.path.join(folder_id["path"], subfolder), level=level + 1)
                for subfolder in subfolders
                if os.path.isdir(os.path.join(folder_id["path"], subfolder))
            ]
        except FileNotFoundError:
            return []
    else:  # folder was collapsed
        folder_id["icon"] = "material-symbols:folder-close"
        return []


# @app.callback(
#     Output({"type": "subfolders", "path": MATCH}, "children"),
#     [Input({"type": "folder", "path": MATCH}, "n_clicks")],
#     [State({"type": "folder", "path": MATCH}, "id")],
# )
# def toggle_folder(n_clicks, folder_id):
#     level = folder_id["path"].count(os.sep) - root_folder.count(os.sep)
#     if n_clicks % 2 == 1:  # folder was expanded
#         try:
#             subfolders = os.listdir(folder_id["path"])
#             return [
#                 folder_div(os.path.join(folder_id["path"], subfolder), level=level + 1)
#                 for subfolder in subfolders
#                 if os.path.isdir(os.path.join(folder_id["path"], subfolder))
#             ]
#         except FileNotFoundError:
#             return []
#     else:  # folder was collapsed
#         return []


if __name__ == "__main__":
    app.run_server(debug=True)
