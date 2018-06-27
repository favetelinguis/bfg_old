import json
import logging
from pyrsistent import freeze, thaw, v, m, pvector, pmap, pdeque, get_in, PRecord, field, pmap_field
from . import betfair_access_layer
from rx.concurrency import ThreadPoolScheduler
from rx import Observable
from datetime import datetime, timedelta

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
     'orders': {}
     })

window_size = 1
runner_cache = freeze(
    {'selectionId': None,
     'status': None,
     'runnerName': None,
     'backPrice': None,
     'layPrice': None,
     'sumBacked': None,
     'backReturn': None,
     'avgBackPrice': None,
     'sumLaid': None,
     'layLiability': None,
     'avgLayPrice': None,
     'hedgeStake': None,
     'hedge': None,
     'sumUnMatchedLay': None,
     'sumUnMatchedBack': None,
     'availableToBack': [],
     'availableToLay': []
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
        agg = agg.transform(['orders', order['betId']], order)

    return agg


def calculate_sums(selectionId, orders):
    sumBacked = 0
    sumLaid = 0
    backReturn = 0
    layLiability = 0
    sumUnmatchedBack, sumUnMatchedLay = 0, 0
    for betId, order in orders.items():
        if order['selectionId'] == selectionId:
            if order['side'] == 'BACK':
                sumBacked += order['sizeMatched']
                sumUnmatchedBack += order['sizeRemaining']
                backReturn += order['sizeMatched'] * order['averagePriceMatched']
            else:
                sumLaid += order['sizeMatched']
                sumUnMatchedLay += order['sizeRemaining']
                layLiability += order['sizeMatched'] * order['averagePriceMatched']
    return sumBacked, backReturn, sumLaid, layLiability, sumUnmatchedBack, sumUnMatchedLay


def calculate_averages(sumBacked, backReturn, sumLaid, layLiability):
    averageBackPrice, averageLayPrice = 0, 0
    if sumBacked > 0:
        averageBackPrice = backReturn / sumBacked
    if sumLaid > 0:
        averageLayPrice = layLiability / sumLaid
    return averageBackPrice, averageLayPrice


def calculate_hedge(backReturn, layLiability, backPrice, layPrice, sumBacked, sumLaid):
    hedgeStake, hedge = 0, 0
    if backReturn > layLiability:  # hedge excess return
        hedgeStake = (backReturn - layLiability) / layPrice
        if hedgeStake != 0:
            hedge = hedgeStake - (sumBacked - sumLaid)

    if layLiability > backReturn:  # hedge excess layLiability
        hedgeStake = (layLiability - backReturn) / backPrice
        if hedgeStake != 0:
            hedge = hedgeStake - (sumBacked - sumLaid)

    return hedgeStake, hedge


def val_or_zero(values):
    if len(values) > 0:
        return values[0]['price']
    return 0.


def update_derived_values(state):
    """
    Need to update
     'backPrice'
     'layPrice'
     'sumBacked'
     'backReturn'
     'avgBackPrice'
     'sumLaid'
     'layLiability'
     'avgLayPrice'
     'sumUnMatchedLay'
     'sumUnMatchedBack'
     'hedgeStake'
     'hedge'
    :param state:
    :return:
    """
    # TODO slow since for each runner i have to go over all order can be more efficient
    # TODO only update the values that has changed not all values every time
    # TODO need to handle when the avaliableToBakc/lay is an empty list
    e = state.evolver()
    ers = state['runners'].evolver()
    for selectionId, runner in state['runners'].items():
        er = runner.evolver()
        backPrice = val_or_zero(get_in(['availableToBack'], runner))
        er['backPrice'] = backPrice
        layPrice = val_or_zero(get_in(['availableToLay'], runner))
        er['layPrice'] = layPrice
        sumBacked, backReturn, sumLaid, layLiability, sumUnmatchedBack, sumUnMatchedLay = calculate_sums(selectionId,
                                                                                                         state[
                                                                                                             'orders'])
        er['sumBacked'] = sumBacked
        er['backReturn'] = backReturn
        er['sumLaid'] = sumLaid
        er['layLiability'] = layLiability
        er['sumUnmatchedBack'] = sumUnmatchedBack
        er['sumUnmatchedLay'] = sumUnMatchedLay
        averageBackPrice, averageLayPrice = calculate_averages(sumBacked, backReturn, sumLaid, layLiability)
        er['avgBackPrice'] = averageBackPrice
        er['avgLayPrice'] = averageLayPrice
        hedgeStake, hedge = calculate_hedge(backReturn, layLiability, backPrice, layPrice, sumBacked, sumLaid)
        er['hedgeStake'] = hedgeStake
        er['hedge'] = hedge
        ers[selectionId] = er.persistent()
    e['runners'] = ers.persistent()
    return e.persistent()


def sliding_window_updater(agg, new, window_size=1):
    if new.type == 'card':
        updated = update_card_in_cache(agg, new)
    elif new.type == 'market':
        updated = update_market_in_cache(agg, new, window_size)
    elif new.type == 'order':
        updated = update_order_in_cache(agg, new)
    else:
        raise ValueError('streamdata has unknown type')
    # TODO do i have to do this for all message types?
    return update_derived_values(updated)


def update_chache(grp_observable):
    return grp_observable \
        .scan(sliding_window_updater, seed=cache) \
        # .replay(lambda obs: obs.share())
    # TODO check the runners.exs legth, obs can be non existing
    # .filter(lambda x: len(x) == window_size)


def filling_the_hole_agent(grp_observable):
    """
    Read in orders and ladder, check if there are any empty or shallow places
    around best price, if so place stop bets there. Now monitor the market,
    if the price get closer to my stop place an order just before.
    Case 1: I place order and the stop gets hit
    Case 2: The stop gets filled before I can place order
    Case 3: I place order but stop is never filled the market turns

    Make sure to have a check to see if there is an open order, then I should
    not be able to place another bet.

    Make sure I am aware of key prices and trade them differently.

    Make sure I check the book description about hedgeing and greening

    Tag the place bets with the correct labels, stop etc

    Maybe not the whole stop order is filled even if the whole enty if filled

    Dont back at crossover prices 2, 3, 4, 6, 10, 20, 30, 50 and 100
    Because if i back i want to price to drop and if it goues up i loose more then if it drops

    :param market_books: tuple of market books for 1 market
    :return:
    """
    def make_decicion(state):
        utc_now = datetime.utcnow()
        market_start = datetime.strptime(state['marketStartTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
        # Make sure status is OPEN and inplay is false
        type = 'NOP'
        data = None
        selection = None
        if state['status'] == 'OPEN' and not state['inplay']:
            seconds_to_start = (market_start - utc_now).total_seconds()
            # Make sure there are no orders on the market
            for selectionId, runner in state['runners'].items():
                if runner['status'] == 'ACTIVE':
                    selection = selectionId
                    break
            if len(state['orders']) == 0:
                type = 'STOP'
                data = {
                    'size': 2,
                    'price': 1.01,
                    'market_id': state['marketId'],
                    'selection_id': selection,
                    'side': 'LAY',
                    'ref': 'stop'
                }
        return pmap({'type': type, 'data': data})
    return grp_observable.map(make_decicion)


def get_merged_root():
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
    return get_merged_root() \
        .let(market_splitter, function=update_chache) \
        .replay(lambda o: o.share())


def strategy(observable):
    """
    Returns a map that is used to decide what betting action to take.
    :return:
    """
    return observable \
        .let(market_splitter, function=filling_the_hole_agent) \
        .filter(lambda d: d['type'] != 'NOP') # Remove all decision that are no op

def take_action(decision):
    if decision['type'] == 'NOP':
        log.warning('NOP should be filtered and now show up here')
    elif decision['type'] == 'STOP':
        log.info(f"PLACING STOP AT: {json.dumps(thaw(decision['data']))}")
        # betfair_access_layer.place_order(**thaw(decision['data']))
