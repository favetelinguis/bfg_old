import os
from sqlalchemy import create_engine
import betfairlightweight
from trader import BFG
from config import config
from db import setup_db

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
    bfg.start()
