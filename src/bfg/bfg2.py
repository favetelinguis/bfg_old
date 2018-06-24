import logging
from pyrsistent import freeze, thaw, v, m, pvector, pmap, pdeque
from . import betfair_access_layer
from rx.concurrency import ThreadPoolScheduler
from rx import Observable

log = logging.getLogger(__name__)
main_worker = ThreadPoolScheduler(1)

cache = freeze(
    {'marketId': None,
     'status': None,
     'inplay': None,
     'marketName': None,
     'marketStartTime': None,
     'totalMatched': None,
     'runners': {},
     'orders': {
         'stop': {},
         'entry': {},
         'runaway': {}
     }})

window_size = 1
runner_cache = freeze(
    {'selectionId': None,
     'status': None,
     'runnerName': None,
     'totalMatched': [],
     'exs': []}
)

exs_cache = freeze(
    {
        'tradedVolume': None,
        'availableToBack': None,
        'availableToLay': None,
        'publishTime': None
    }
)


def update_card_in_cache(agg, new):
    assert agg['marketId'] is None, 'card can only be set on empty cache as first value'
    data = new.data
    e = agg.evolver()
    e['marketId'] = data['marketId']
    e['marketName'] = data['marketName']
    e['marketStartTime'] = data['marketStartTime']
    for runner in data['runners']:
        re = runner_cache.evolver()
        re['selectionId'] = runner['selectionId']
        re['runnerName'] = runner['runnerName']
        e['runners'] = e['runners'].set(runner['selectionId'], re.persistent())
    return e.persistent()


def update_market_in_cache(agg, new, window_size):
    data = new.data
    e = agg.evolver()
    e['status'] = data['status']
    e['inplay'] = data['inplay']
    e['totalMatched'] = data['totalMatched']
    new_data = e.persistent()
    for runner in data['runners']:
        new_data = new_data.transform(['runners', runner['selectionId'], 'status'], runner['status'])
    return new_data


def update_order_in_cache(agg, new):
    """
    takes in an order and selects if its a stop, entry,
    or runaway exit by checking the customerOrderRef.
    If it is a new order an enty is created in the map, if its an update
    the old order is replaced
    :param agg:
    :param new:
    :return:
    """
    data = new.data
    for order in data['currentOrders']:
        agg = agg.transform(['orders', order['customerOrderRef'], order['betId']], order)

    return agg


def sliding_window_updater(agg, new, window_size=1):
    if new.type == 'card':
        updated = update_card_in_cache(agg, new)
    elif new.type == 'market':
        updated = update_market_in_cache(agg, new, window_size)
    elif new.type == 'order':
        updated = update_order_in_cache(agg, new)
    else:
        raise ValueError('streamdata has unknown type')
    return updated


def update_chache(grp_observable):
    return grp_observable \
        .scan(sliding_window_updater, seed=cache) \
        # .replay(lambda obs: obs.share())
    # TODO check the runners.exs legth, obs can be non existing
    # .filter(lambda x: len(x) == window_size)


def filling_the_hole_agent(observable):
    """
    Read in orders and ladder, check if there are any empty or shallow places
    around best price, if so place stop bets there. Now monitor the market,
    if the price get closer to my stop place an order just before.
    Case 1: I place order and the stop gets hit
    Case 2: The stop gets filled before I can place order
    Case 3: I place order but stop is never filled the market turns
    :param market_books: tuple of market books for 1 market
    :return:
    """
    import random
    import time
    time.sleep(random.randint(1, 12))
    if random.randint(1, 10) > 5:
        return 'DO TRADE'  # Should not return anything if we decide not to do trade
    return 'NO TRADE'


def get_meged_root():
    merged_root = Observable.merge(betfair_access_layer.market_observable,
                                   betfair_access_layer.order_observable) \
        .start_with(*betfair_access_layer.todays_racecard) \
        .observe_on(main_worker)
    return merged_root


def market_splitter(observable, function):
    """
    :param observable:
    :return: grp observables grouped on marketId caches
    """
    return observable \
        .group_by(lambda stream_data: stream_data.marketId) \
        .flat_map(function)


def cache_emitter():
    """
    Base observable that emits observables containing the cache for
    a specif market, holds the latests emission
    :return:
    """
    return get_meged_root() \
        .let(market_splitter, function=update_chache)


def strategy():
    """
    Returns a map that is used to decide what betting action to take.
    :return:
    """
    return cache_emitter() \
        .let(market_splitter, function=filling_the_hole_agent) \
        .filter(lambda action: action == 'DO TRADE')
