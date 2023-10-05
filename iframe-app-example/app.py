# Simple Dash app to cycle between DSA WSIs and change the image shown on an
# embedded iframe of HistomicsUI. Mainly looking to deal with the access token
# so we can view private images without being logged out everytime we switch
# images.
from dash_mantine_components import Select
from dash import html, Dash, callback, Output, Input

DSA_URL = "https://styx.neurology.emory.edu"
API_KEY = "F24SKHTasyuZI1TihEjQU8peB4mzwBYl0tZOTHy6"

app = Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            Select(
                label="Select WSI:",
                placeholder="",
                id="wsi-select",
                value="651ec46e8691f6a5f529c9ff",
                data=[
                    {"label": "E20-106_1 Tau.svs", "value": "651ec46e8691f6a5f529c9ff"},
                    {"label": "E20-106_14 HE.svs", "value": "651ec48b8691f6a5f529ca04"},
                    {
                        "label": "E20-106_15 Syn.svs",
                        "value": "651ec4fa8691f6a5f529ca09",
                    },
                ],
            )
        ),
        html.Div("This is where the HistomicsUI iframe should go!", id="iframe"),
    ]
)


@callback(Output("iframe", "children"), Input("wsi-select", "value"))
def return_iframe(img_id):
    return html.Iframe(src=DSA_URL)


if __name__ == "__main__":
    app.run(debug=True)
