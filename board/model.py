import pandas as pd
from sqlalchemy.sql import select

def get_graph_data(db):
    #query = select([tables.inference_time])
    query = 'SELECT * FROM inference_time'
    df = pd.read_sql(query, db)
    data = df.time_elapsed
    print(data)
    return data

def get_data(db):
    #query = select([tables.market_book])
    query = 'SELECT * FROM market_book'
    df = pd.read_sql(query, db)
    data = df.tail(1).market_id
    return data
