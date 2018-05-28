import logging
import queue
import time

import betfairlightweight
from betfairlightweight import StreamListener
from betfairlightweight.streaming.stream import MarketStream
from rx import Observable, Observer

logging.basicConfig(level=logging.INFO)

class HistoricalStream(MarketStream):
    # create custom listener and stream

    def __init__(self, listener, observable):
        super(HistoricalStream, self).__init__(listener)
        self.observable = observable

    def on_process(self, market_books):
        [self.observable.on_next(market_book) for market_book in market_books]
        time.sleep(2)


class HistoricalListener(StreamListener):
    def __init__(self, observable):
        super(HistoricalListener, self).__init__()
        self.observable = observable
    def _add_stream(self, unique_id, stream_type):
        if stream_type == 'marketSubscription':
            return HistoricalStream(self, self.observable)


class Client:
    def __init__(self, path='/Users/henriklarsson/repos/betfair_liam_data/marketdata/streaming/7/1.142492699'):
        listener, self.observable = create_listener()
        self.trading = betfairlightweight.APIClient('username', 'password', app_key='app_key')
        self.stream = self.trading.streaming.create_historical_stream(
            directory=path,
            listener=listener,
        )

    def __enter__(self):
        self.trading.login()
        self.stream.start(async=False)
        return self.output_queue

    def __exit__(self, type, value, tb):
        self.trading.logout()
        self.stream.stop()

def create_listener():
    def observe_market_books(observable):
        listener = HistoricalListener(observable, max_latency=1e100)
    return listener, Observable.create(observe_market_books).share()
