import time
from rx import Observable
from rx.testing import TestScheduler, ReactiveTest, marbles
from rx.concurrency import ThreadPoolScheduler
import bfg

on_next = ReactiveTest.on_next
on_completed = ReactiveTest.on_completed
on_error = ReactiveTest.on_error
subscribe = ReactiveTest.subscribe
subscribed = ReactiveTest.subscribed
disposed = ReactiveTest.disposed
created = ReactiveTest.created

sheduler = ThreadPoolScheduler(4)


def test_switch_map():
    '''
    Looks like the calculation is not aborted it is just NOT emitted, so if I do any side affect in a switch_map
    that side affect will still be done even if calculation has timed out, so make sure to do side effect after.
    '''

    def side_effect(value):
        if value % 2 == 0:
            time.sleep(4)
        print('Side: ', value)  # this should not happen

    Observable.interval(2000) \
        .switch_map(lambda i: Observable.just(i).do_action(side_effect).subscribe_on(sheduler)) \
        .subscribe(lambda x: print('Main', x), print)
    time.sleep(15)


def test_marbles():
    r = Observable.from_marbles('1-2-3-4-|').map(lambda x: str(x + 1)).to_blocking().to_marbles()
    print(r)


def test_group_by():
    # TODO element_selector could provide my mapper function here to turn the data into immutable after this point
    # this is where all my agent logic should go
    items = ['a', 'b', 'vv', 'aaa','aaa','ggg']
    Observable.from_(items).group_by(lambda s: len(s)) \
        .flat_map(lambda grp: grp.count().map(lambda c: (grp.key, c))) \
        .subscribe(print)


def test_sliding_window():
    from collections import deque
    window_size = 3

    def adder(agg, val):
        agg.append(val)
        return agg

    Observable.of(1, 2, 3, 4, 5, 6, 7, ) \
        .scan(adder, seed=deque(maxlen=window_size)) \
        .filter(lambda x: len(x) == window_size) \
        .map(tuple) \
        .subscribe(print)


def test_distinct_until_change():
    '''
    Test that we can specify some part that should be distinct not the whole message
    :return:
    '''
    keyCode = 'keyCode'
    codes = [
        {'a': 1, keyCode: 38},  # // up
        {'a': 2, keyCode: 38},  # // up
        {'a': 3, keyCode: 40},  # // down
        {'a': 4, keyCode: 40},  # // down
        {'a': 5, keyCode: 37},  # // left
        {'a': 6, keyCode: 39},  # // right
        {'a': 7, keyCode: 37},  # // left
        {'a': 8, keyCode: 39},  # // right
        {'a': 9, keyCode: 66},  # // b
        {'a': 10, keyCode: 65}  # // a
    ]
    Observable.from_(codes).distinct_until_changed(comparer=lambda x,y: x[keyCode] == y[keyCode]).subscribe(print)

def test_hot_emit_latest():
    '''
    Test how i can have ahot observable and every time someone new subscribe they get
    the last emission until a new one? Maybe just buffer or winow works?
    :return:
    '''
    o1 = Observable.interval(10000).share()
    o2 = Observable.interval(4000).share()
    o = Observable.combine_latest(o1.start_with(10),o2.start_with(10),lambda a,b: a + b).replay(lambda x: x.share(), buffer_size=1)
    o.subscribe(lambda x: print('Im 1: ', x))
    time.sleep(6)
    print('Nr 2 subscribing')
    o.subscribe(lambda x: print('Im 2: ', x))
    time.sleep(100)


def test_split_list():
    # flat_map does not preserve order
    Observable.of([1, 2, 3], [4, 5, 6]).flat_map(lambda l: Observable.from_list(l)).subscribe(print)


def test_retry_and_error_handler_in_network_layer():
    pass


def test_named_tuple_from_map():
    DEFU = bfg.namedtuple_with_defaults('defu', ['a', 'b', 'c'])
    source = {'a': 1, 'b': 2, 'd': 4, 'c': 3}
    new = bfg.mapper(DEFU, source)
    assert new == DEFU(a=1, b=2, c=3)
