import dash_html_components as html
import dash_core_components as dcc

from controller import init_controllers


def init_layout(app, db):
    app.layout = html.Div([
        html.Div([
            # Page header
            html.H1(id='h1-text')
        ]),
        dcc.Interval(
            id='updater',
            interval=1*1000
            )
    ])
    init_controllers(app, db)


class GUI():
    def __init__(self, app, db):
        self.db = db
        self.app = app
        init_layout(app, db)
