import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL
from pymongo import MongoClient
from dash import dcc
import json

DSA_BASE_Url = "https://styx.neurology.emory.edu/api/v1"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/style.css"])


window_size_component = html.Div(
    [
        dcc.Store(id="window-size"),
        dcc.Interval(id="interval-component", interval=2 * 1000, n_intervals=0),  # in milliseconds
        # Your other components go here
    ]
)


def getThumbnail(imgId):
    url = f"{DSA_BASE_Url}/item/{imgId}/tiles/thumbnail"
    return url


# MongoDB setup
client = MongoClient("localhost:27017")
db = client["ItemSetData"]
collection = db["records"]

# Define the image and page sizes for each option
sizes = {
    "small": {"image_size": "128px", "page_size": 30},
    "medium": {"image_size": "192px", "page_size": 20},
    "large": {"image_size": "256px", "page_size": 12},
}


images_per_row = {
    "small": 5,
    "medium": 3,
    "large": 2,
}


def DataViewComponent(db_collection, sizes):
    @app.callback(
        Output("cards-container", "children"),
        Output("pagination", "max_value"),
        Input("size-selector", "value"),
        Input("pagination", "active_page"),
    )
    def update_cards(selected_size, active_page):
        image_size = sizes[selected_size]["image_size"]
        page_size = sizes[selected_size]["page_size"]

        start = (active_page - 1) * page_size

        data = list(db_collection.find().skip(start).limit(page_size))

        cards_and_tooltips = []

        for index, item in enumerate(data):
            card_id = f"card-{index}"
            column_width = 12 // images_per_row[selected_size]  # Adjust column width based on image size
            cards_and_tooltips.append(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardImg(
                                src=getThumbnail(item["_id"]),
                                top=True,
                                style={"height": image_size, "width": image_size},
                            ),
                            dbc.CardBody(
                                [
                                    html.H6(item["name"], className="card-title no-wrap"),
                                    html.P("Some Content should go here", className="card-text"),
                                ]
                            ),
                        ],
                        className="mb-4",
                        id=card_id,  # add id to each card
                    ),
                    md=column_width,  # Adjusted column width
                )
            )
            cards_and_tooltips.append(
                dbc.Tooltip(
                    f"Row: {index//3 + 1}, Column: {(index%3) + 1}",
                    target=card_id,
                )
            )

        cards = dbc.Row(cards_and_tooltips, justify="start")

        total_data_count = db_collection.count_documents({})  # Get total number of documents in the collection

        max_value = (total_data_count + page_size - 1) // page_size  # Round up to account for any remaining items

        return cards, max_value

    size_selector = dbc.RadioItems(
        id="size-selector",
        options=[{"label": size.capitalize(), "value": size} for size in sizes],
        value="small",  # Default value
        inline=True,
    )

    pagination = dbc.Pagination(id="pagination", size="lg", active_page=1, max_value=20)

    clicked_card = html.Div(id="clicked-card")  # display clicked card id

    return html.Div([html.Div(size_selector), html.Div(id="cards-container"), html.Div(pagination), clicked_card])


app.clientside_callback(
    """
    function(n_intervals) {
        return dash_clientside.clientside.update_window_dimensions();
    }
    """,
    Output("window-size", "data"),
    [Input("interval-component", "n_intervals")],
)


@app.callback(
    Output("clicked-card", "children"),
    [Input({"type": "card", "index": ALL}, "n_clicks")],
    [State({"type": "card", "index": ALL}, "id")],
)
def display_click_data(n_clicks, ids):
    clicked_id = next((id_["index"] for nc, id_ in zip(n_clicks, ids) if nc), None)
    if clicked_id is not None:
        return f"Clicked card id: {clicked_id}"
    return "No card clicked yet"


app.layout = html.Div([html.Div(id="wininfo"), window_size_component, DataViewComponent(collection, sizes)])


@app.callback(
    Output({"type": "card", "index": ALL}, "className"),
    [Input({"type": "card", "index": ALL}, "n_clicks")],
    [State({"type": "card", "index": ALL}, "className")],
)
def change_card_color(n_clicks, class_names):
    new_class_names = []
    for nc, class_name in zip(n_clicks, class_names):
        if nc:
            new_class_names.append(class_name + " clicked")
        else:
            new_class_names.append(class_name.replace(" clicked", ""))
    return new_class_names


@app.callback(Output("wininfo", "children"), [Input("window-size", "data")])
def update_winsize(window_size):
    # Use window_size['width'] and window_size['height'] to set the size of your graph
    ##print(window_size)
    return html.Div(json.dumps(window_size))  # None  # return html.div(window_size)


if __name__ == "__main__":
    app.run_server(debug=True)
