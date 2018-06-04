import dash_html_components as html
import dash_core_components as dcc


def init_views(app):
    app.layout = html.Div([
        html.Div([
            # Page header
            html.H1(id='h1-text')
        ]),
        dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='updater',
            interval=1*1000
            )
    ])
