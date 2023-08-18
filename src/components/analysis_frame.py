"""
The analysis tab / frame. This div contains the CLI tab, the HistomicsUI iFrame,
and the reports tab - unsure what kind of UI these will be in.
"""
from dash import html
import dash_bootstrap_components as dbc
from .histomicsui import histomicsui
from .clis import clis
from .results import results

tab1 = dbc.Card(dbc.CardBody([clis]))

tab2 = dbc.Card(dbc.CardBody([histomicsui]))

tab3 = dbc.Card(dbc.CardBody([results]))

analysis_frame = html.Div(
    dbc.Tabs(
        [
            dbc.Tab(tab1, label="Tab 1", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(tab2, label="HistomicsUI", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(tab3, label="Report", activeTabClassName="fw-bold fst-italic"),
        ]
    ),
    id="analysis-frame",
)
