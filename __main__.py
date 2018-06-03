import os
import time

import dash
from sqlalchemy import create_engine
import betfairlightweight

from trader import BFG
from config import config
from db import setup_db
from gui import GUI

if __name__ == '__main__':

    # Setup config
    config = config[os.getenv('BFG_CONFIG') or 'default']

    # Setup database
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
    db = engine.connect()
    setup_db(engine)

    # Setup betfair
    betfair = betfairlightweight.APIClient(
        config.BETFAIR_USER, config.BETFAIR_PASSWORD,
        app_key=config.BETFAIR_APP_KEY)
    betfair.login()

    # Setup trader
    bfg = BFG()
    bfg.use_exchange(betfair)
    bfg.use_config(config)
    bfg.use_db(db)
    bfg.use_agent()
    import multiprocessing
    p = multiprocessing.Process(target=bfg.start)
    p.start()

    # Setup dash
    app = dash.Dash()
    app.css.append_css({
        "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
    })
    gui = GUI(app, db)
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
