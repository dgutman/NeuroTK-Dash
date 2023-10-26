"""
The analysis tab / frame. This div contains the CLI tab, the HistomicsUI iFrame,
and the reports tab - unsure what kind of UI these will be in.
"""
from dash import html, dcc
import dash_bootstrap_components as dbc
from .histomicsui import histomicsui
from .clis import dsa_cli_view_layout
from .report import report
from ...utils.settings import COLORS

tab1 = dbc.Card(
    dbc.CardBody([dsa_cli_view_layout]),
    style={"backgroundColor": COLORS["background-secondary"]},
)

tab2 = dbc.Card(
    dbc.CardBody([histomicsui]),
    style={"backgroundColor": COLORS["background-secondary"]},
)

tab3 = dbc.Card(
    dbc.CardBody([report]), style={"backgroundColor": COLORS["background-secondary"]}
)

analysis_frame = html.Div(
    [
        dcc.Store(id="report-store", data={}),
        dbc.Tabs(
            [
                dbc.Tab(
                    tab1, label="Analysis", activeTabClassName="fw-bold fst-italic"
                ),
                dbc.Tab(
                    tab2, label="HistomicsUI", activeTabClassName="fw-bold fst-italic"
                ),
                dbc.Tab(tab3, label="Report", activeTabClassName="fw-bold fst-italic"),
            ]
        ),
    ],
    id="analysis-frame",
    style={"backgroundColor": COLORS["background-secondary"]},
)
