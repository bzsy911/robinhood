import os
import time
import pickle
import pandas as pd
import robin_stocks as r
from dotenv import load_dotenv
from arxiv.utils import close_time, now
import json
from typing import List






# login
def login():
    load_dotenv()
    r.login(os.getenv('EMAIL'), os.getenv('PASSWORD'))


# get watchlist
def watchlist():
    wl = [t['instrument'] for t in r.get_watchlist_by_name()]
    return wl


# get order history, replace to newest ticker


# get holdings
# stocks = list(r.build_holdings().keys())
# portfolio = [Stock([Order(o) for o in orders if o['ticker'] == t][::-1]) for t in tickers]


# create table for watchlist
# info to get: price, dividend, 52w high, 52w low, fair value, buy rating, volatility, popularity, sector
# additional info for bought: last buy, last sell, total profit
def old_friend(url, all_orders):
    return url in [s['url'] for s in all_orders]


def get_ratings(ticker):
    rating = r.get_ratings(ticker)
    votes = tuple(rating['summary'].values())
    return votes


def get_info_for_watchlist(urls):
    # WIP
    tickers = [r.get_symbol_by_url(u) for u in urls]
    fundamentals = r.get_fundamentals(tickers)
    # quotes = r.get_quotes(tickers)
    ratings = [get_ratings(t) for t in tickers]

    columns = ['52w_high', '52w_low', 'divident_yield', 'sector', 'industry']
    res = [[f['high_52_weeks'], f['low_52_weeks'], f['dividend_yield'], f['sector'], f['industry']] for f in fundamentals]
    # res += [[q['last_trade_price'], q[]] for q in quotes]



class Robin:

    def __init__(self):
        load_dotenv()
        r.login(os.getenv('EMAIL'), os.getenv('PASSWORD'))

    def record_portfolio(self):
        stocks = list(r.build_holdings().keys())
        data = [stocks+['Time']]
        start = now()
        market_close = close_time()
        print('Data Recording Starts at:', start)
        print('Scheduled Close Time at:', time.strftime("%b %d %Y %H:%M:%S", time.localtime(market_close)))

        while time.time() < market_close():
            try:
                prices = r.stocks.get_latest_price(stocks)
                print(time.strftime("%H:%M:%S", time.localtime()),
                      [s + ": " + str(round(float(x), 2)) for s, x in zip(stocks, prices)])
                data.append(prices + [time.localtime()])
                time.sleep(5)
            except Exception as msg:
                print(f"Error in request: {msg}")

        df = pd.DataFrame(data)
        end = now()
        df.to_excel(f'output/price_{start}_{end}.xlsx')
        print('data saved')


def build_hist():
    all_orders = r.get_all_stock_orders()

    with open('ticker_dict.json') as f:
        ticker_dict = json.load(f)
    all_orders = [order for order in all_orders if float(order['cumulative_quantity']) != 0]
    for order in all_orders:
        order['amount'] = -1 * float(order['executed_notional']['amount'])
        order['quantity'] = int(float(order['cumulative_quantity']))
        if order['side'] == 'sell':
            order['amount'] *= -1
            order['quantity'] *= -1
        order['fees'] = -1 * float(order['fees'])
        order['time'] = order['last_transaction_at']
        order['price'] = float(order['average_price'])
        order['cost'] = order['amount'] + order['fees']
        if order['instrument'] not in ticker_dict:
            order['ticker'] = r.get_symbol_by_url(order['instrument'])
            ticker_dict[order['instrument']] = order['ticker']
        else:
            order['ticker'] = ticker_dict[order['instrument']]

    with open('ticker_dict.json', 'w') as f:
        json.dump(ticker_dict, f)

    with open('ticker_map.json') as f:
        ticker_map = json.load(f)
    for order in all_orders:
        order['ticker'] = ticker_map.get(order['ticker'], order['ticker'])

    df = pd.DataFrame(all_orders)
    df = df[['time', 'ticker', 'price', 'quantity', 'cost']]
    print(df)

    df.to_excel(f'output/order_all.xlsx')
    return all_orders


def build_hist_dev():
    df = pd.read_excel('output/order_all.xlsx', 'Sheet1')

    with open('ticker_map.json') as f:
        ticker_map = json.load(f)
    df['ticker'] = df['ticker'].apply(lambda x: ticker_map.get(x, x))

    tb = df.groupby('ticker')[['quantity', 'cost']].sum()
    tb['trades'] = df.groupby('ticker')['ticker'].count()
    hold = tb[tb['quantity'] != 0]
    unhold = tb[tb['quantity'] == 0]
    print(hold)
    print(unhold)
    return


def depth(hist):
    stack = []
    quant_hist = [o.quantity for o in hist]
    for n in quant_hist:
        if n > 0:
            stack.append(n)
        else:
            n = -n
            while stack and stack[-1] <= n:
                n -= stack.pop()
            if n > 0:
                stack[-1] -= n
    return len(stack)


class Order:

    def __init__(self, r_order: dict):
        self.ticker = r_order['ticker']
        self.url = r_order['url']
        self.time = r_order['time']
        self.quantity = r_order['quantity']
        self.price = r_order['price']
        self.fees = r_order['fees']
        self.cost = r_order['cost']
        self.meta = r_order


class Spectrum:

    def __init__(self, avg_cost, holdings: List[int]):
        self.avg_cost = avg_cost
        self.spectrum = [0.5, 0.625, 0.75, 0.875, 1, 1.1, 1.15, 1.2, 1.5]
        self.eccentric = [200, 1000]
        self.holdings = holdings
        self.result = self.result()

    def gen_spec(self, scope, pc):
        # scope = 0, 1, 2 is the index of self.avg_cost
        return None if self.avg_cost[scope] is None else round(self.avg_cost[scope] * pc, 2)

    def gen_ecc(self, scope, n):
        return None if self.avg_cost[scope] is None or self.holdings[scope] == 0 \
            else round((self.avg_cost[scope] * self.holdings[scope] + n)/self.holdings[scope], 2)

    def fill_spectrum(self):
        return [[self.gen_spec(scope, pc) for pc in self.spectrum] for scope in range(3)]

    def fill_eccentric(self):
        return [[self.gen_ecc(scope, n) for n in self.eccentric] for scope in range(3)]

    def result(self):
        return [s+e for s, e in zip(self.fill_spectrum(), self.fill_eccentric())]


class StockFeatures:

    def __init__(self, ticker):
        self.ticker = ticker
        self.company = None
        self._52w_low = None
        self._52w_high = None
        self.pe_ratio = None
        self.dividend = None
        self.last_price = None

        if ticker is not None:
            fundamentals, instruments, prices = self.validate()
            if len(fundamentals) * len(instruments) * len(prices) > 0:
                self.build(fundamentals[0], instruments[0], prices[0])

    def validate(self):
        try:
            fundamentals = r.get_fundamentals(self.ticker)
            instruments = r.get_instruments_by_symbols(self.ticker)
            prices = r.get_latest_price(self.ticker)
        except:
            fundamentals = []
            instruments = []
            prices = []
        return fundamentals, instruments, prices

    def build(self, fundamental, instrument, price):
        self.company = instrument['simple_name']
        self._52w_low = fundamental['low_52_weeks']
        self._52w_high = fundamental['high_52_weeks']
        self.pe_ratio = fundamental['pe_ratio']
        self.dividend = fundamental['dividend_yield']
        self.last_price = float(price)


class Stock:

    def __init__(self, history: List[Order] = None, ticker=None, url=None):
        self.url = url
        self.feature = StockFeatures(ticker)
        self.history = []
        self.holding = 0  # current number of shares holding
        self.outcome = None  # current total cost/revenue
        self.balance = None  # outcome + holding * last_price
        self.spectrum = Spectrum([None, None, None], [0, 0, 0])
        self.last_round = []  # the last round of orders
        self.depth = 0
        self.recommend_buy_strategy = None  # {quantity, price, reason}
        self.recommend_sell_strategy = None  # {quantity, price, reason}
        self.representation = None

        if history:
            self._build_from_history(history)
        elif url:
            ticker = r.get_instrument_by_url(url)['symbol']
            self._build_from_ticker(ticker)

        self.representation = self._build_representation()

    def _build_from_ticker(self, ticker):
        self.feature = StockFeatures(ticker)

    def _build_from_history(self, history):
        if len(set([order.ticker for order in history])) > 1:
            raise Exception("History contains more than 1 stocks!")
        self._init(history[0])
        for order in history[1:]:
            self._trade(order)

    def _init(self, order):
        self.history.append(order)
        self.url = order.url
        self._build_from_ticker(order.ticker)

        # building by order history
        self.holding = order.quantity  # current number of shares holding
        self.outcome = order.cost  # current total cost/revenue
        self.balance = self.outcome + self.feature.last_price * self.holding \
            if self.feature.last_price is not None else self.outcome  # outcome + last_price * holding
        self.spectrum = Spectrum([order.price for _ in range(3)], [self.holding for _ in range(3)])
        self.last_round = [order]  # the stack keeping track of oldest holdings
        self.depth = 1

        self.recommend_buy_strategy = {'quantity': order.quantity,
                                       'price': self.spectrum.result[0][3],  # global 87.5%
                                       'reason': '...'}
        self.recommend_sell_strategy = {'quantity': order.quantity,
                                        'price': self.spectrum.result[0][6],  # global 115%
                                        'reason': '...'}

    def _trade(self, order):
        self.history.append(order)
        self.last_round.append(order)

        self.holding += order.quantity  # current number of shares holding
        self.outcome += order.cost  # current total cost/revenue
        self.balance = self.outcome + self.feature.last_price * self.holding \
            if self.feature.last_price is not None else self.outcome  # outcome + last_price * holding
        if self.holding > 0:
            avg_global = -1 * min(self.outcome, 0)/self.holding
            avg_last_round = -1 * min(sum([o.cost for o in self.last_round]), 0)/self.holding
        else:
            avg_global = None
            self.last_round = []
            avg_last_round = None

        if order.quantity > 0:  # buy
            last_buy = order.price
            last_buy_quantity = order.quantity
        else:
            last_buy = self.spectrum.avg_cost[2]  # if sell, inherit the old last buy price
            last_buy_quantity = self.spectrum.holdings[2]

        self.spectrum = Spectrum([avg_global, avg_last_round, last_buy],
                                 [self.holding, self.holding, last_buy_quantity])
        self.depth = depth(self.last_round)

        # self.recommend_buy_strategy = {'quantity': order.quantity, 'price': self._88pc_last_buy, 'reason': '...'}
        # self.recommend_sell_strategy = {'quantity': order.quantity, 'price': self._115pc_last_buy, 'reason': '...'}

    def _build_representation(self):
        df = pd.DataFrame([o.meta for o in self.history])
        df = df[['time', 'ticker', 'price', 'quantity', 'cost']]

        msg = f"""
{self.feature.ticker}
Current Holding: {self.holding}
Current Outcome: {self.outcome}
Current Balance: {self.balance}
Trading History: {df}

Current Price: {self.feature.last_price}
Global Avg Cost: {self.spectrum.avg_cost[0]}
Last Round Avg Cost: {self.spectrum.avg_cost[1]}
Last Buy Price: {self.spectrum.avg_cost[2]}
Depth: {self.depth}
85% Last Buy: {self.spectrum.result[2][3]}
110% Last Buy: {self.spectrum.result[2][5]}
110% Global Cost: {self.spectrum.result[0][5]}

"""
        print(msg)
        return msg


if __name__ == "__main__":
    login()
    orders = build_hist()
    tickers = set(map(lambda x: x['ticker'], orders))
    portfolio = [Stock([Order(o) for o in orders if o['ticker'] == t][::-1]) for t in tickers]
    with open('output/my_portfolio.obj', 'wb') as f:
        pickle.dump(portfolio, f)

    p = []
    for stock in sorted(portfolio, key=lambda x: x.outcome):
        p.append(stock.representation)

    with open('output/my_portfolio.txt', 'w+') as f:
        f.write('\n'.join(p))
