from dash import html
from dash import Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
from ..utils.settings import DSA_BASE_URL, gc
import dash

### This will generate a dataview component, similar to what we have been using in Webix
## It expects a list of dictionaries, and then we can have various templates depending on
## what type of visualization we want, can also add the keys to display on the template, etc

# Define the image and page sizes for each option
sizes = {
    "small": {"image_size": "128px", "page_size": 12},
    "medium": {"image_size": "192px", "page_size": 10},
    "large": {"image_size": "256px", "page_size": 5},
}


images_per_row = {
    "small": 6,
    "medium": 5,
    "large": 3,
}


def getThumbnailUrl(imageId, encoding="PNG", height=128):
    ### Given an imageId, turns this into a URL to fetch the image from a girder server
    ## including the token
    thumb_url = f"{DSA_BASE_URL}/item/{imageId}/tiles/thumbnail?encoding={encoding}&height={height}&token={gc.token}"
    return thumb_url


def generate_cards(subset, selected_size):
    cards_and_tooltips = []

    for index, item in enumerate(subset):
        card_id = f"card-{index}"
        column_width = 12 // images_per_row[selected_size]

        cards_and_tooltips.append(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardImg(
                            src=getThumbnailUrl(item["_id"]),
                            top=True,
                            style={
                                "height": sizes[selected_size]["image_size"],
                                "width": sizes[selected_size]["image_size"],
                            },
                        ),
                        dbc.CardBody(
                            [
                                html.H6(item["name"], className="card-title no-wrap"),
                                # html.P(
                                #     "Some Content should go here", className="card-text"
                                # ),
                            ]
                        ),
                    ],
                    className="mb-4",
                    style={"width": 192, "height": 192, "margin": 2},
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

    return cards_and_tooltips


def generateDataViewLayout(itemSet):
    size_selector = dbc.RadioItems(
        id="size-selector",
        options=[{"label": size.capitalize(), "value": size} for size in sizes],
        value="small",  # Default value
        inline=True,
    )

    initial_max_page = (len(itemSet) // sizes["small"]["page_size"]) + (
        1 if len(itemSet) % sizes["small"]["page_size"] > 0 else 0
    )
    pagination = dbc.Pagination(
        id="pagination", size="sm", active_page=1, max_value=initial_max_page
    )

    # We will initially display only the first page of cards. The callback will handle subsequent updates.
    active_page = 1
    start_idx = (active_page - 1) * sizes["small"]["page_size"]
    end_idx = start_idx + sizes["small"]["page_size"]
    # cards_and_tooltips = generate_cards(itemSet[start_idx:end_idx], "small")

    # cards = dbc.Row(cards_and_tooltips, justify="start")
    return [
        html.Div([size_selector, pagination]),  # Put these controls in a Div at the top
        html.Div(id="cards-container"),  # This Div will be populated by the callback
    ]

    # return [size_selector, pagination, html.Div()]


@callback(
    [Output("pagination", "max_value"), Output("cards-container", "children")],
    [Input("pagination", "active_page"), Input("size-selector", "value")],
    [State("filteredItem_store", "data")],
)
def update_cards_and_pagination(active_page, selected_size, itemSet):
    if not itemSet or not active_page or not selected_size:
        return dash.no_update, dash.no_update

    cards_per_page = sizes.get(selected_size, {}).get("page_size", 0)
    if not cards_per_page:
        return dash.no_update, dash.no_update

    start_idx = (active_page - 1) * cards_per_page
    end_idx = start_idx + cards_per_page

    cards_and_tooltips = generate_cards(itemSet[start_idx:end_idx], selected_size)
    cards = dbc.Row(cards_and_tooltips, justify="start")

    max_page = (len(itemSet) // cards_per_page) + (
        1 if len(itemSet) % cards_per_page > 0 else 0
    )

    return max_page, cards
