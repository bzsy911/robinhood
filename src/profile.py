import pandas as pd
from src import api


class Profile:

    def __init__(self, ticker):
        self.ticker = ticker
        self.company = None
        self._52w_low = None
        self._52w_high = None
        self.pe_ratio = None
        self.dividend = None
        self.last_price = None

        if ticker is not None:
            fundamentals, prices = self.validate()
            if len(fundamentals) * len(prices) > 0:
                self.build(fundamentals[0], prices[0])

    def validate(self):
        try:
            fundamentals = api.get_fundamentals(self.ticker)
            prices = api.get_latest_price(self.ticker)
        except:
            fundamentals = []
            prices = []
        return fundamentals, prices

    def build(self, fundamental, price):
        self._52w_low = fundamental['low_52_weeks']
        self._52w_high = fundamental['high_52_weeks']
        self.pe_ratio = fundamental['pe_ratio']
        self.dividend = fundamental['dividend_yield']
        self.last_price = float(price)


class Present(Profile):

    def __init__(self, history):
        self.history = history.sort_values(by='time')
        super().__init__(self.history.iat[0, 1])
        self.current_trades, self.last_trades, self.total_prev_profit = self.get_recent_trades()
        self.current_stack = self.get_current_stack()
        self.lock_depth = len(self.current_stack)
        self.current_avg_cost, self.buy_in_price, self.sp10, self.sp15 = self.get_limits()
        self.strategy = self.get_strategy()

    def get_strategy(self):
        if self.last_price >= self.current_stack.iat[-1, 2]:
            dist_sp10 = round(100 * (self.sp10/self.last_price - 1), 2)
            dist_sp15 = round(100 * (self.sp15/self.last_price - 1), 2)
            strategy = f"""
{self.ticker}
{self.current_stack}
Price: {self.last_price}
SELL: {self.sp10 if self.last_price < self.sp10 else self.sp15} for {10 if self.last_price < self.sp10 else 15}% profit
UP {dist_sp10 if self.last_price < self.sp10 else dist_sp15}% 
"""
        else:
            dist_buy_in = round(100 *(1 - self.buy_in_price/self.last_price))
            strategy = f"""
{self.ticker}
{self.current_stack}
Current Price at {self.last_price}
BUY: {self.buy_in_price}
DOWN {dist_buy_in}%
"""
        return strategy

    def get_limits(self):
        current_avg_cost = -sum(self.current_stack.cost) / sum(self.current_stack.quantity)
        buy_in_price = (0.85 - 0.1 * (self.lock_depth - 1)) * current_avg_cost / self.lock_depth
        last_bought_at = self.current_stack.iat[-1, 2]
        sp10 = 1.1 * last_bought_at
        sp15 = 1.15 * last_bought_at
        return round(current_avg_cost, 2), round(buy_in_price, 2), round(sp10, 2), round(sp15, 2)

    def get_recent_trades(self):
        quantity_list = self.history.quantity.tolist()
        partial_sum = [sum(quantity_list[:i+1]) for i in range(len(quantity_list))]
        if 0 not in partial_sum:
            current_trades = self.history
            last_trades = None
            total_prev_profit = 0
        elif partial_sum.count(0) == 1:
            clean_up_point = partial_sum.index(0)
            current_trades = self.history.iloc[clean_up_point + 1:, :]
            last_trades = self.history.iloc[:clean_up_point + 1, :]
            total_prev_profit = sum(last_trades.cost)
        else:
            clean_up_points = [idx for idx, val in enumerate(partial_sum) if val == 0]
            current_trades = self.history.iloc[clean_up_points[-1] + 1:, :]
            last_trades = self.history.iloc[clean_up_points[-2] + 1:clean_up_points[-1] + 1, :]
            total_prev_profit = sum(self.history.cost) - sum(current_trades.cost)
        return current_trades, last_trades, total_prev_profit

    def get_current_stack(self):
        stack = []
        quantity_list = self.current_trades.quantity.tolist()
        for idx, n in enumerate(quantity_list):
            if n > 0:
                stack.append([n, idx])
            else:
                n = -n
                while stack and stack[-1][0] <= n:
                    n -= stack.pop()[0]
                if n > 0:
                    stack[-1][0] -= n
        current_stack = self.current_trades.iloc[[x[1] for x in stack], :]
        current_stack.quantity = [x[0] for x in stack]
        return current_stack


class Ex(Profile):
    pass


class Prospect(Profile):
    pass


def build_presents(order_df=None):
    if not order_df:
        order_df = pd.read_csv('output/order_all.csv')
    tb = order_df.groupby('ticker')[['quantity']].sum()
    return [order_df[order_df['ticker'] == ticker] for ticker in tb[tb['quantity'] != 0].index]


def build_exs(order_df=None):
    if not order_df:
        order_df = pd.read_csv('output/order_all.csv')
    tb = order_df.groupby('ticker')[['quantity']].sum()
    return [order_df[order_df['ticker'] == ticker] for ticker in tb[tb['quantity'] == 0].index]


def build_prospects(watch_list):
    pass


if __name__ == '__main__':
    order = build_presents()[0]
    order = order.sort_values(by='time')
    present_aapl = Present(order)
    print(present_aapl.strategy)
