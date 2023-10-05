# Simple Dash app to cycle between DSA WSIs and change the image shown on an
# embedded iframe of HistomicsUI. Mainly looking to deal with the access token
# so we can view private images without being logged out everytime we switch
# images.
import dash
from dash import html, Dash, callback, Output, Input
from dash_mantine_components import Select

DSA_URL = "https://megabrain.neurology.emory.edu"
API_KEY = "pSXuuP3qhWOW5ZqoOLhQMYuDRj9HNPD0FD9qyGm0"

app = Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            Select(
                label="Select WSI:",
                placeholder="",
                id="wsi-select",
                value="651ebc456b4fa9ed76d42a3e",
                data=[
                    {"label": "E20-106_1 Tau.svs", "value": "651ebc456b4fa9ed76d42a3e"},
                    {"label": "E20-106_14 HE.svs", "value": "651ebc456b4fa9ed76d42a3c"},
                    {
                        "label": "E20-106_15 Syn.svs",
                        "value": "651ebc456b4fa9ed76d42a3a",
                    },
                ],
            )
        ),
        html.Div("This is where the HistomicsUI iframe should go!", id="iframe"),
    ]
)


@callback(Output("iframe", "children"), Input("wsi-select", "value"))
def return_iframe(img_id):
    return html.Div(img_id)


if __name__ == "__main__":
    app.run(debug=True)
