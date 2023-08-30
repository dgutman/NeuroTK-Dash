"""
Popup component to add dataset.
"""
from dash import html, Output, Input, callback, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from typing import List
from ..utils.api import get_datasets_list

add_dataset_popup = dbc.Modal(
    [
        dbc.ModalHeader('Add Dataset'),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(
                    dmc.Select(
                        [], id='dataset-dropdown', clearable=True, 
                        placeholder='Select dataset.', label='Select dataset:'
                    ), 
                ),
                dbc.Col(
                    html.Button(
                        [html.I(className="fa-solid fa-plus")], disabled=True, 
                        id='add-dataset-bn', title='add dataset to project'
                    ),
                    width='auto'
                ),
                dbc.Col(
                    html.Button(
                        [html.I(className='fa-solid fa-arrows-rotate')],
                        id='refresh-dataset-list-bn',
                        title='refresh the dataset list',
                    ),
                    width='auto'
                )
            ]),
            html.Br(),
            dmc.Textarea(
                placeholder='Dataset metadata.', autosize=True,
                id='dataset-info'    
            ),
        ])
    ],
    id='add-dataset-popup',
    is_open=False,
    fullscreen=False
)


@callback(
    [
        Output('dataset-info', 'value'),
        Output('add-dataset-bn', 'disabled')
    ],
    Input('dataset-dropdown', 'value'),
    State('dataset-item-store', 'data'),
    prevent_initial_call=True
)
def populate_dataset_info(value, data):
    """
    
    """
    for dataset in data:
        if dataset['_id'] == value:
            # Found the dataset, return its description.
            if dataset['description']:
                string = f"Description: {dataset['description']}"

                # string += f'Filters:\n{json.dumps()}'
                if 'meta' in dataset and 'filters' in dataset['meta']:
                    string += '\n\nFilters:\n'

                    for k, v in dataset['meta']['filters'].items():
                        string += f'  {k}: {v}\n'
                return string, False
            else:
                return 'No description for dataset found.', False
    
    return '', True


@callback(
    Output('dataset-dropdown', 'data'),
    Input('dataset-item-store', 'data'),
)
def populate_dataset_dropdown(data: List[dict]) -> List[dict]:
    """
    Populate the Dataset dropdown when the dataset item store changes.

    Args:
        data: List of dictionaries with metadata on the datasets.

    Returns:
        List of dictionaries with value key (id of the dataset item) and 
        label key (user name and dataset name).
    
    """
    # Populate the dropdown.
    options = []

    for dataset in data:
        options.append({'value': dataset['_id'], 'label': dataset['path']})

    return options


@callback(
    Output('add-dataset-popup', 'is_open'),
    Input('add-dataset', 'n_clicks'),
    [
        State('projects-store', 'data'),
        State('projects-dropdown', 'value')
    ],
    prevent_initial_call=True
)
def open_add_dataset_popup(n_clicks: int, data, value) -> bool:
    """
    Open the add dataset popup and populate the select with available
    datasets.
    
    Args:
        n_clicks: Number of times button has been clicked.

    Returns:
        Always returns True to open up the menu.
    """
    if n_clicks:
        return True


@callback(
    [
        Output('add-dataset', 'disabled'),
        Output('add-dataset', 'title'),
        Output('add-dataset', 'style')
    ],
    Input('tasks-dropdown', 'value'),
    prevent_initial_call=True
)
def change_dataset_bn_state(value):
    """
    Disable or enable the "+ Dataset" button. This should be disabled when there
    is a task selected.

    """
    if value:
        return True, 'De-select task to allow adding more project datasets.', \
            {'background': '#db5e5e'}
    else:
        return False, 'Add dataset', {'background': '#7df097'}


@callback(
    Output('dataset-item-store', 'data'),
    Input('refresh-dataset-list-bn', 'n_clicks'),
    prevent_initial_call=True
)
def refresh_dataset_store(n_clicks):
    """
    Refresh the dataset list store.

    """
    if n_clicks:
        return get_datasets_list()
