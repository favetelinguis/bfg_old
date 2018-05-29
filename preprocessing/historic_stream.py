import logging
import zipfile
import glob
import shutil
import os, errno
import pandas as pd

import betfairlightweight
from betfairlightweight import StreamListener
from betfairlightweight.streaming.stream import MarketStream

"""
Data needs to be downloaded from:
    https://historicdata.betfair.com
"""

# setup logging
logging.basicConfig(level=logging.INFO)

# create trading instance (no need to put in correct details)
trading = betfairlightweight.APIClient('username', 'password', app_key='key')


class HistoricalStream(MarketStream):
    # create custom listener and stream

    def __init__(self, listener, output_path):
        super(HistoricalStream, self).__init__(listener)
        self.output_path = output_path
        with open(output_path, 'w') as output:
            output.write('Time,MarketId,Status,Inplay,SelectionId,LastPriceTraded\n')

    def on_process(self, market_books):
        with open(self.output_path, 'a') as output:
            for market_book in market_books:
                for runner in market_book.runners:
                    output.write('%s,%s,%s,%s,%s,%s\n' % (
                        market_book.publish_time, market_book.market_id, market_book.status, market_book.inplay,
                        runner.selection_id, runner.last_price_traded or ''
                    ))

class HistoricalListener(StreamListener):
    def __init__(self, output_path, max_latency):
        super(HistoricalListener, self).__init__(max_latency=max_latency)
        self.output_path = output_path
    def _add_stream(self, unique_id, stream_type):
        if stream_type == 'marketSubscription':
            return HistoricalStream(self, self.output_path)


def generate_csv(file_name):
    base_dir = '/Users/henriklarsson/repos/betfair_liam_small_test'
    csv_dir = base_dir + '/csv_files'
    raw_file_path = base_dir + '/unziped_files/' + file_name
    output_path = csv_dir + '/' + file_name + '.csv'
    if not os.path.exists(csv_dir):
        try:
            os.makedirs(csv_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    listener = HistoricalListener(
        output_path,
        max_latency=1e100
    )
    stream = trading.streaming.create_historical_stream(
        directory=raw_file_path,
        listener=listener
    )
    stream.start(async=False)
    return True


def unzip_file(path):
    target_dir = '/Users/henriklarsson/repos/betfair_liam_small_test/unziped_files'
    parts = path[:-4].split('/')
    file_name = parts[-1]
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    with zipfile.ZipFile(path, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    return file_name

def remove_unziped_files():
    shutil.rmtree('/Users/henriklarsson/repos/betfair_liam_small_test/unziped_files', ignore_errors=True)

if __name__ is '__main__':
    from dask import compute, delayed
    import dask.threaded
    zip_files = glob.glob('/Users/henriklarsson/repos/betfair_liam_small_test/*.zip')

    results = []
    for zip_file in zip_files:
        raw_file_name = delayed(unzip_file)(zip_file)
        result = delayed(generate_csv)(raw_file_name)
        results.append(result)

    compute(*results, scheduler='threads')
    remove_unziped_files()
    
