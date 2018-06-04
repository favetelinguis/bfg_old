import os
import dash
from sqlalchemy import create_engine
from controller import init_controllers
from view import init_views

# Setup database
engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI'), echo=True)
db = engine.connect()

# Setup dash
app = dash.Dash(__name__)
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})
init_views(app)
init_controllers(app, db)

if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
)
