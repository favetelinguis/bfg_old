import sys
import json
import time
import signal
import os
import logging
from pyrsistent import freeze, thaw, v, m, pvector, pmap, pdeque, get_in

from rx import Observable
from rx.concurrency import ThreadPoolScheduler
from rx.core import Disposable
from rx.disposables import CompositeDisposable, BooleanDisposable

from . import config, betfair_access_layer, cache_emitter, strategy, take_action

# Setup config
config = config[os.getenv('BFG_CONFIG') or 'default']

# Setup logging
logging.basicConfig(filename='bfg.log', level=config.LOG_LEVEL)
log = logging.getLogger(__name__)

gui_worker = ThreadPoolScheduler(1)

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass


def signal_handler(signum, frame):
    log.info('Caught signal %d' % signum)
    raise ServiceExit


def build_orders(next_market):

    orders = {
        '1:Stops   ': thaw(next_market['orders']['stop']),
        '2:Entrys  ': thaw(next_market['orders']['entry']),
        '3:Runaways': thaw(next_market['orders']['runaway']),
        '4:Greenup' : thaw(next_market['orders']['runaway']),
        '5:Runaways': thaw(next_market['orders']['runaway']),
        '6:Runaways': thaw(next_market['orders']['runaway']),
    }
    return orders


def build_runners(runners):
    data = {}
    for selectionId, runner in runners.items():
        unmatched_back = runner['sumUnmatchedBack']
        unmatched_lay = runner['sumUnmatchedLay']
        r = f"Backed {runner['sumBacked']} @ {runner['avgBackPrice']}" + \
            f" Laid {runner['sumLaid']} @ {runner['avgLayPrice']}" + \
            f" Hedge Value {runner['hedge']}" + \
            f" UnMatched LAY:{unmatched_lay}, BACK:{unmatched_back}" + \
            f" Status {runner['status']}"
        data['{:25.25}'.format(runner['runnerName'])] = r
    return data


def build_gui(data):
    all_markets = sorted(data.items(), key=lambda t: t[1]['marketStartTime'])
    all_markets = [d[1] for d in all_markets if d[1]['status'] != 'CLOSED']
    if len(all_markets) == 1:
        nm = 'CURRENT MARKET IS TODAY`S LAST'
    else:
        nm = f"{all_markets[1]['marketId']} {all_markets[1]['marketStartTime']} {all_markets[1]['marketName']}"
    next_market = all_markets[0]
    gui = {
        # TODO add info about exposere liability and hedgin stakes green up check book
        '1:Market ID    ': next_market['marketId'],
        '2:Start Time   ': next_market['marketStartTime'],
        '3:Market Name  ': next_market['marketName'],
        '4:Status       ': next_market['status'],
        '5:Inplay       ': next_market['inplay'],
        '6:Total Matched': next_market['totalMatched'],
        '7:Runners      ': build_runners(next_market['runners']),
        '9:Next market--': nm,
    }
    return gui


def render(data):
    d = build_gui(data)
    adf = os.system("clear")
    return json.dumps(d, indent=4, sort_keys=True)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    log.info('Starting BFG')
    # Make sure to init bfg before I start using it
    disposables = None
    try:
        betfair_access_layer.login(config.BETFAIR_USER, config.BETFAIR_PASSWORD, config.BETFAIR_APP_KEY)
        cache = cache_emitter()
        strategy_disposable = cache.let(strategy).subscribe(take_action, log.error)
        gui_disposable = cache \
            .observe_on(gui_worker)\
            .scan(lambda agg, new: agg.transform([new['marketId']], new), seed=m()) \
            .map(render) \
            .subscribe(print, log.error, lambda: log.warning('!!!THE STREAM COMPLETED'))
        disposables = CompositeDisposable(strategy_disposable, gui_disposable)
        while True:
            time.sleep(0.5)
    except ServiceExit:
        print('Shutting down takes 5 secs')
        disposables.dispose()
        betfair_access_layer.shut_down()
