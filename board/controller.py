from dash.dependencies import Input, Output, Event
import plotly.graph_objs as go

from model import get_data, get_graph_data


def init_controllers(app, db):
    @app.callback(
        Output('live-graph', 'figure'),
        events=[Event('updater', 'interval')]
    )
    def render_graph():
        y = get_graph_data(db)
        x = list(range(len(y)))
        data = go.Scatter(
            x=x,
            y=y,
            name='Elapsed time for trade decision in seconds',
            mode='lines+markers'
        )
        return {'data': [data], 'layout': go.Layout(
            title='Elapsed time for trade decision in seconds',
            xaxis=dict(range=[min(x), max(x)]),
            yaxis=dict(range=[min(y), max(y)]),)}

    @app.callback(
        Output('h1-text', 'children'),
        events=[Event('updater', 'interval')]
    )
    def render_text():
        data = get_data(db)
        return data
