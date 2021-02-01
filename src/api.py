import os
import robin_stocks as r
from dotenv import load_dotenv

load_dotenv()
r.login(os.getenv('EMAIL'), os.getenv('PASSWORD'))


def get_symbol_by_url(url):
    return r.get_symbol_by_url(url)


def get_all_stock_orders():
    return r.get_all_stock_orders()


def get_fundamentals(ticker):
    return r.get_fundamentals(ticker)


def get_instruments_by_symbols(ticker):
    return r.get_fundamentals(ticker)


def get_latest_price(ticker):
    return r.get_latest_price(ticker)
