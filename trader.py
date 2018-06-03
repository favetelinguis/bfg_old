import db as tables
import datetime as dt
from sqlalchemy import create_engine


class BFG():
    db = None
    client = None
    config = None

    def start(self):
        # Must create db in the thread that is going to use it
        engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI, echo=True)
        self.db = engine.connect()
        import time
        #while True:
        for i in range(1000):
            mbs = [{'market_id': str(i), 'start_time': dt.datetime.now()}]
            ins = tables.market_book.insert()
            self.db.execute(ins, mbs)
            time.sleep(5)

    def use_exchange(self, client):
        self.client = client

    def use_config(self, config):
        self.config = config

    def use_db(self, db):
        self.db = db

    def use_agent(self):
        pass
