import json
import logging
import time
from collections import namedtuple

import betfairlightweight
from betfairlightweight.filters import (
    limit_order,
    place_instruction,
    market_filter,
    streaming_market_filter,
    streaming_market_data_filter,
)

from datetime import date, timedelta

from rx import Observable

log = logging.getLogger(__name__)

# https://developer.betfair.com/exchange-api/betting-api-demo/
RACE_CARD_MARKET_FILTER = market_filter(
    event_type_ids=['7'],  # Horse racing
    market_type_codes=['WIN'],
    market_countries=['GB'],
    market_start_time={
        'from': f'{time.strftime("%Y-%m-%d")}T00:00:00Z',
        # 'to': f'{time.strftime("%Y-%m-%d")}T23:59:00Z'
        'to': f'{str(date.today() + timedelta(days=1))}T23:59:00Z'
    }
)

StreamData = namedtuple('stream_data', 'type marketId data')


def create_order_streamdata(marketId, data):
    return StreamData(type='order', marketId=marketId, data=data)


def create_market_streamdata(marketId, data):
    return StreamData(type='market', marketId=marketId, data=data)


def create_card_streamdata(marketId, data):
    return StreamData(type='card', marketId=marketId, data=data)


def add_marketId(market):
    market['marketId'] = market['currentOrders'][0]['marketId']
    return market


def market_order_merge(markets, orders, race_card):
    return [markets, orders, [r._data for r in race_card]]


class BetfairAccessLayer:
    def __init__(self):
        self._client = None
        self._market_observable = None
        self._order_observable = None
        self._todays_racecard = None
        self._market_stream = None
        self._order_stream = None

    def login(self, user, password, app_key):
        assert self._client is None, 'Befair already initialized'
        self._client = betfairlightweight.APIClient(user, password, app_key=app_key)
        self._client.login()  # TODO error handling

    @property
    def todays_racecard(self):
        assert self._client, 'Befair must first be initialized'
        if not self._todays_racecard:
            self._todays_racecard = [create_card_streamdata(marketId=d.market_id, data=d._data) for d in
                                     self.get_todays_racecard()]
        return self._todays_racecard

    @property
    def market_observable(self):
        # TODO emissions not immutable
        assert self._client, 'Befair must first be initialized'
        if not self._market_observable:
            def observe_market(observer):
                class FakeQueue:
                    def put(self, value):
                        observer.on_next(value)

                listener = betfairlightweight.StreamListener(
                    output_queue=FakeQueue(),
                    lightweight=True
                )
                self._market_stream = self._client.streaming.create_stream(
                    listener=listener,
                    description='BFG Market Stream'
                )
                market_filter = streaming_market_filter(
                    market_ids=[market.marketId for market in self.todays_racecard]
                )
                market_data_filter = streaming_market_data_filter(
                    fields=['EX_BEST_OFFERS', 'EX_TRADED', 'EX_TRADED_VOL', 'EX_LTP', 'EX_MARKET_DEF'],
                    ladder_levels=3,  # Market depth
                )
                self._market_stream.subscribe_to_markets(
                    market_filter=market_filter,
                    market_data_filter=market_data_filter,
                    # conflate_ms=1000,
                )
                self._market_stream.start(async=True)

            # use subscribe_on else we are using the market thread for all operations (async False so we use main thread)
            # use share so multiple subscriber can use this observable but we start emitting after the first has subscribed
            self._market_observable = Observable.create(observe_market) \
                .flat_map(Observable.from_) \
                .map(lambda m: create_market_streamdata(marketId=m['marketId'], data=m)) \
                .share()
        return self._market_observable

    @property
    def order_observable(self):
        # TODO emissions not immutable
        assert self._client, 'Befair must first be initialized'
        if not self._order_observable:
            def observe_order(observer):
                class FakeQueue:
                    def put(self, value):
                        observer.on_next(value)

                listener = betfairlightweight.StreamListener(
                    output_queue=FakeQueue(),
                    lightweight=True
                )
                self._order_stream = self._client.streaming.create_stream(
                    listener=listener,
                    description='BFG Order Stream'
                )
                self._order_stream.subscribe_to_orders()
                self._order_stream.start(async=True)

            # Split list of markets into markets and add marketId as field for order so we can group by
            self._order_observable = Observable.create(observe_order) \
                .flat_map(Observable.from_) \
                .map(lambda m: create_order_streamdata(marketId=m['currentOrders'][0]['marketId'], data=m)) \
                .share()
        return self._order_observable

    def shut_down(self):
        self._market_stream._running = False
        self._order_stream._running = False
        time.sleep(5)
        self._market_stream.stop()
        self._order_stream.stop()

    def get_todays_racecard(self):
        # TODO put the request on  a separate thread and return an Observable
        # maybe something like Observable.just(1).map(request check for error and raise error).retry(3) retry 3 times if we get error how to not block?
        card = self._client.betting.list_market_catalogue(
            filter=RACE_CARD_MARKET_FILTER,
            market_projection=[  # 'COMPETITION',
                # 'EVENT',
                # 'EVENT_TYPE',
                # 'MARKET_DESCRIPTION' IS NOT WORKING
                'MARKET_START_TIME',
                'RUNNER_DESCRIPTION',
                # 'RUNNER_METADATA'
            ],
            sort='FIRST_TO_START',
            max_results=2
        )
        assert card, 'The racecard today is empty'
        return card

    # Order examples from https://github.com/liampauling/betfair/blob/master/examples/exampletwo.py
    def place_orders(self, size, price, market_id, selection_id, side, ref):
        order = limit_order(
            size=size,
            price=price,
            persistence_type='LAPSE'
        )
        instruction = place_instruction(
            order_type='LIMIT',
            selection_id=selection_id,
            side=side,
            limit_order=order,
            customer_order_ref=ref
        )
        place_orders = self._client.betting.place_orders(
            market_id=market_id,
            instructions=[instruction]  # list
        )
        # TODO check order.status
        return place_orders

    def update_order(self, order_id):
        instruction = filters.update_instruction(
            bet_id=bet_id,
            new_persistence_type='PERSIST'
        )
        update_order = trading.betting.update_orders(
            market_id=market_id,
            instructions=[instruction]
        )

    def replace_order(self, bet_id):
        instruction = filters.replace_instruction(
            bet_id=bet_id,
            new_price=1.10
        )
        replace_order = trading.betting.replace_orders(
            market_id=market_id,
            instructions=[instruction]
        )

    def cancel_order(self, bet_id):
        instruction = filters.cancel_instruction(
            bet_id=bet_id,
            size_reduction=2.00
        )
        cancel_order = trading.betting.cancel_orders(
            market_id=market_id,
            instructions=[instruction]
        )


betfair_access_layer = BetfairAccessLayer()
