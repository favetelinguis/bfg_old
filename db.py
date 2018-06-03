import datetime as dt

from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime

metadata = MetaData()
market_book = Table('market_book', metadata,
                    Column('market_id', String(15), primary_key=True),
                    Column('start_time', DateTime(), nullable=False),
                    Column('created_on', DateTime(), default=dt.datetime.now),
                    Column('updated_on', DateTime(), default=dt.datetime.now,
                           onupdate=dt.datetime.now))

def setup_db(engine):
    metadata.drop_all(engine)
    metadata.create_all(engine)
