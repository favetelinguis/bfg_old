import db as tables
import datetime as dt


class BFG():
    db = None
    client = None
    config = None

    def start(self):
        # TODO start an infinite loop that every second inserts a value into the database
        # have the dash app read that part of the database every second and print in gui
        import time
        #while True:
        for i in range(1000):
            mbs = [{'market_id': str(i), 'start_time': dt.datetime.now()}]
            ins = tables.market_book.insert()
            self.db.execute(ins, mbs)
            print('HERE I AM AGAIN ON MY OWN')
            time.sleep(5)

    def use_db(self, db):
        self.db = db

    def use_exchange(self, client):
        self.client = client

    def use_config(self, config):
        self.config = config

    def use_db(self, db):
        self.db = db

    def use_agent(self):
        pass
