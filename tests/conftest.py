import pytest

import bfg


@pytest.fixture()
# @pytest.fixture(autouse=True, scope='session')
def bfg_db():
    # bfg.dal.db_init('sqlite:///:memory:?check_same_thread=False')
    bfg.dal.db_init('sqlite:///bfg_test.db?check_same_thread=False')


@pytest.fixture()
def patch_market_catalogue(monkeypatch):
    monkeypatch.setattr(
        #bfg.bal.betfair.betting,
        #'list_market_catalogue',
        bfg.bal.betfair,
        'login',
        lambda: 2
    )

