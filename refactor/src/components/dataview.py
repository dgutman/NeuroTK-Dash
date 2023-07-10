import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
from pymongo import MongoClient


DSA_BASE_Url = "https://styx.neurology.emory.edu/api/v1"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


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

        cards = dbc.Row(
            [
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
                                    html.H4(item["name"], className="card-title"),
                                    html.P("Some Content should go here", className="card-text"),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    md=4,
                )
                for item in data
            ],
            justify="start",
        )

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

    return html.Div([html.Div(size_selector), html.Div(id="cards-container"), html.Div(pagination)])


app.layout = DataViewComponent(collection, sizes)

if __name__ == "__main__":
    app.run_server(debug=True)
