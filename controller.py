from dash.dependencies import Input, Output, Event

from model import get_data

def init_controllers(app, db):

    @app.callback(
        Output('h1-text', 'children'),
        events=[Event('updater', 'interval')]
    )
    def render_text():
        data = get_data(db)
        return data
