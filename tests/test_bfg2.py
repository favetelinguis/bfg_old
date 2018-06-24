import json
import time

from pyrsistent import freeze, thaw, v, m, pvector, pmap, pdeque, get_in
import pytest
from rx import Observable
from rx.testing import TestScheduler, ReactiveTest, marbles
from bfg.betfair import create_card_streamdata, create_market_streamdata, create_order_streamdata
from bfg.bfg2 import sliding_window_updater, cache, runner_cache, exs_cache, update_chache

on_next = ReactiveTest.on_next
on_completed = ReactiveTest.on_completed
on_error = ReactiveTest.on_error
subscribe = ReactiveTest.subscribe
subscribed = ReactiveTest.subscribed
disposed = ReactiveTest.disposed
created = ReactiveTest.created


def test_sliding_window_updater_card_data(stream_data):
    card_data = stream_data[0]
    new_val = sliding_window_updater(cache, card_data)
    assert new_val['marketId'] == card_data.marketId
    assert new_val['marketName'] is not None
    assert new_val['marketStartTime'] is not None
    assert len(new_val['runners']) == len(card_data.data['runners'])


def test_update_cache(stream_data):
    results = []
    Observable.from_(stream_data)\
        .let(update_chache)\
        .do_action(results.append)\
        .subscribe(lambda x: x)
    assert len(results) == 3

def test_ptest():
    m = freeze({'a':2, 'runners':{1:{'a':44},2:{'b':44},3:{'c':66}}})
    m2 = m['runners'][2].set('b', 100)
    e = m.evolver()
    e['a'] = 222
    e['runners'][1]
    m3 = 3


@pytest.fixture(scope='session')
def stream_data():
    with open('resources/aping_observable_output_in_progress.json') as f:
        data = json.load(f)

    new_data = [create_card_streamdata(data[2][0]['marketId'], data[2][0]),
                create_market_streamdata(data[0][0]['marketId'], data[0][0]),
                create_order_streamdata(data[1][0]['currentOrders'][0]['marketId'], data[1][0])]
    return new_data


@pytest.fixture(scope='session')
def stream_datas_observable(stream_data):
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(on_next(180, stream_data[0]), on_next(180, stream_data[1]),
                                         on_next(180, stream_data[2]))
    return Observable.from_(stream_data)
