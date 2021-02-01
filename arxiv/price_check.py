import os
import pandas as pd
import pandasql as ps

import robin_stocks as r
from dotenv import load_dotenv
import json


def login():
    load_dotenv()
    r.login(os.getenv('EMAIL'), os.getenv('PASSWORD'))


def check():
    data = pd.read_excel('data/price_set.xlsx').to_numpy().tolist()
    last_price = list(map(float, r.get_latest_price([d[0] for d in data])))
    res = []
    for d, lp in zip(data, last_price):
        ticker, price, out, cost, buy, hand = d
        if lp > price:
            if lp > price*(1+out):
                stg = 'Sell'
            elif 1.03 * lp > price*(1+out):
                stg = 'High'
            else:
                stg = 'Keep'
            res.append([ticker, stg, round(100 * (lp/price - 1), 2), round(lp, 2), round(price*(1+out), 2)])
        else:
            if lp < cost*buy:
                stg = 'Buy'
            elif 0.97 * lp < cost*buy:
                stg = 'Low'
            else:
                stg = 'Keep'
            res.append([ticker, stg, round(100 * (lp/cost - 1), 2), round(lp, 2), round(cost*buy, 2)])

    sell = sorted([t for t in res if t[1] == 'Sell'], key=lambda x: x[4]/x[3], reverse=True)
    buy = sorted([t for t in res if t[1] == 'Buy'], key=lambda x: x[4]/x[3])
    high = sorted([t for t in res if t[1] == 'High'], key=lambda x: x[4]/x[3])
    low = sorted([t for t in res if t[1] == 'Low'], key=lambda x: x[4]/x[3], reverse=True)
    keep = sorted([t for t in res if t[1] == 'Keep'], key=lambda x: x[2], reverse=True)

    ls = list(zip([sell, buy, high, low, keep],
                  ['Ready to Sell:', 'Ready to Buy:', 'Close to Sell:', 'Close to Buy:', 'Keep Waiting:']))

    for i in range(5):
        # set 5 if want to print Keeps
        s, txt = ls[i]
        if s:
            print(txt)
            for t in s:
                print(t[0], f'{t[2]}%', t[3], t[4], f'{round((t[4]/t[3]-1)*100,2)}%')
            print()
    return


def check_2():
    data = pd.read_excel('data/price_set.xlsx').to_numpy().tolist()
    last_price = list(map(float, r.get_latest_price([d[0] for d in data])))
    res = []
    for d, lp in zip(data, last_price):
        ticker, price, _, _, _, hand = d
        res.append((ticker, round((lp - price) * hand)))
    res.sort(key=lambda x: x[1], reverse=True)
    for item in res:
        print(item)
    return


def get_info_for_watchlist():
    # WIP
    wl = [t['instrument'] for t in r.get_watchlist_by_name()]
    tickers = [r.get_symbol_by_url(u) for u in wl]
    fundamentals = [r.get_fundamentals(t)[0] for t in tickers]
    # print(fundamentals)
    quotes = r.get_quotes(tickers)
    # ratings = [get_ratings(t) for t in tickers]

    columns = ['52w_high', '52w_low', 'divident_yield', 'sector', 'industry', 'last_price']
    res = [[f['high_52_weeks'], f['low_52_weeks'], f['dividend_yield'], f['sector'], f['industry']] for f in fundamentals]
    res += [[q['last_trade_price']] for q in quotes]
    # print([[q['symbol'], q['has_traded']] for q in quotes])
    return


def get_hist(start='2018'):
    hist = pd.read_excel('output/order_all.xlsx')
    print(hist)


if __name__ == '__main__':
    login()
    check()
    # check_2()
    # get_info_for_watchlist()
    # get_hist()
