from flask import Blueprint

main = Blueprint('main', __name__)

from . import market_api, account_api, error
