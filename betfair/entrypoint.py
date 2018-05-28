import betfair as bf
import time

if __name__ is '__main__':
    with bf.Client() as source:
        source.subscribe(lambda value: print("Received {0}".format(value)))
        time.sleep(1000000)
