import db as tables
import datetime as dt
from sqlalchemy import create_engine
from collections import deque


class BFG():
    db = None
    client = None
    config = None
    market_books = deque(maxlen=10)
    # TODO have whole racecard in memory of this class

    def start(self):
        # Must create db in the thread that is going to use it
        engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI, echo=True)
        self.db = engine.connect()
        import time
        #while True:
        for i in range(1000):
            self.market_books.append(i)
            mbs = [{'market_id': str(i), 'start_time': dt.datetime.now()}]
            # TODO put database writes in futures
            ins = tables.market_book.insert()
            self.db.execute(ins, mbs)
            t0 = time.time()
            time.sleep(5)
            elapsed = time.time() - t0
            print('ELAPSED', elapsed)
            elapsed_persist = [{'time_elapsed': elapsed}]
            ins = tables.inference_time.insert()
            self.db.execute(ins, elapsed_persist)


    def use_exchange(self, client):
        self.client = client

    def use_config(self, config):
        self.config = config

    def use_db(self, db):
        self.db = db

    def use_agent(self):
        pass
