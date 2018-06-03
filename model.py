import pandas as pd
from sqlalchemy.sql import select
import db as tables


def get_data(db):
    query = select([tables.market_book])
    df = pd.read_sql(query, db)
    data = df.tail(1).market_id
    print(type(data), data)
    return data
