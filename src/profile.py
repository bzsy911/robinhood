import pandas as pd
from src import api
from src.utils import pct_round


class Profile:

    def __init__(self, ticker):
        self.profile = {'Ticker': ticker}

        if ticker is not None:
            fundamentals, prices = self.validate()
            if len(fundamentals) * len(prices) > 0:
                self.build_basic(fundamentals[0], prices[0])

    def validate(self):
        try:
            fundamentals = api.get_fundamentals(self.profile['Ticker'])
            prices = api.get_latest_price(self.profile['Ticker'])
        except:
            fundamentals = []
            prices = []
        return fundamentals, prices

    def build_basic(self, fundamental, price):
        self.profile.update({'52w_Low': fundamental['low_52_weeks'],
                             '52w_High': fundamental['high_52_weeks'],
                             'PE_Ratio': fundamental['pe_ratio'],
                             'Dividend': fundamental['dividend_yield'],
                             'Current_Price': float(price)})
        return


class Present(Profile):

    def __init__(self, history):
        self.history = history.sort_values(by='time')
        super().__init__(self.history.iat[0, 1])
        self.build_profile()

    def build_profile(self):
        self.get_recent_trades()
        self.get_current_stack()
        self.get_limits()
        self.get_strategy()

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
        self.profile.update({'Current_Trades': current_trades,
                             'Holding': sum(quantity_list),
                             'Last_Trades': last_trades,
                             'Total_Prev_Profit': total_prev_profit})
        return

    def get_current_stack(self):
        stack = []
        quantity_list = self.profile['Current_Trades'].quantity.tolist()
        for idx, n in enumerate(quantity_list):
            if n > 0:
                stack.append([n, idx])
            else:
                n = -n
                while stack and stack[-1][0] <= n:
                    n -= stack.pop()[0]
                if n > 0:
                    stack[-1][0] -= n
        current_stack = self.profile['Current_Trades'].iloc[[x[1] for x in stack], :]
        current_stack.quantity = [x[0] for x in stack]
        self.profile.update({'Current_Stack': current_stack,
                             'Lock_Depth': len(current_stack)})
        return

    def get_limits(self):
        current_avg_cost = -sum(self.profile['Current_Stack'].cost) / sum(self.profile['Current_Stack'].quantity)
        buy_in_price = (0.85 - 0.1 * (self.profile['Lock_Depth'] - 1)) * current_avg_cost / self.profile['Lock_Depth']
        last_bought_at = self.profile['Current_Stack'].iat[-1, 2]
        self.profile.update({'Current_Avg_Cost': round(current_avg_cost, 2),
                             'Buy_in_Price': round(buy_in_price, 2),
                             'Last_Bought_at': round(last_bought_at, 2),
                             'Last_Bought_Change': pct_round(self.profile['Current_Price'] / last_bought_at - 1, 2),
                             'sp10': round(1.1 * last_bought_at, 2),
                             'sp15': round(1.15 * last_bought_at, 2),
                             'sp20': round(1.2 * last_bought_at, 2),
                             'sp30': round(1.3 * last_bought_at, 2),
                             'sp50': round(1.5 * last_bought_at, 2)})
        return

    def get_strategy(self):
        if self.profile['Current_Price'] >= self.profile['Last_Bought_at']:
            if 1.03 * self.profile['Current_Price'] < self.profile['sp10']:
                strategy = 'wait'
            elif self.profile['Current_Price'] < self.profile['sp10']:
                strategy = 'watch SELL'
            elif self.profile['Current_Price'] < self.profile['sp50']:
                strategy = 'SELL'
            else:
                strategy = '50%+ SELL'
            gap, target, percent = ([(1 - self.profile['Current_Price'] / target, target, percent/100)
                                     for target, percent in [(self.profile[f'sp{x}'], x) for x in [10, 15, 20, 30, 50]]
                                     if self.profile['Current_Price'] <= target] +
                                    [(0, self.profile['sp50'],
                                      self.profile['Current_Price'] / self.profile['Last_Bought_at'] - 1)])[0]
        else:
            if self.profile['Current_Price'] > self.profile['Buy_in_Price']:
                gap = self.profile['Buy_in_Price'] / self.profile['Current_Price'] - 1
                target = self.profile['Buy_in_Price']
                percent = 0.85 - 0.1 * (self.profile['Lock_Depth'] - 1)
                strategy = 'wait' if 0.97 * self.profile['Current_Price'] >= self.profile['Buy_in_Price'] \
                    else 'watch BUY'
            else:
                gap = 0
                target = self.profile['Buy_in_Price']
                percent = 0.85 - 0.1 * (self.profile['Lock_Depth'] - 1)
                strategy = 'BUY' if 2 * self.profile['Current_Price'] >= self.profile['Buy_in_Price'] else '50%- BUY'
        self.profile.update({'Strategy': strategy,
                             'Gap': pct_round(gap, 2),
                             'Next_Target': target,
                             'Target_%': pct_round(percent)})
        sort = gap if 'watch' in strategy else self.profile['Current_Price'] / self.profile['Last_Bought_at'] - 1
        self.profile.update({'Sort': sort})
        return


class Ex(Profile):
    pass


class Prospect(Profile):
    pass


def build_exs(order_df=None):
    if not order_df:
        order_df = pd.read_csv('output/order_all.csv')
    tb = order_df.groupby('ticker')[['quantity']].sum()
    return [order_df[order_df['ticker'] == ticker] for ticker in tb[tb['quantity'] == 0].index]


def build_prospects(watch_list):
    pass


if __name__ == '__main__':
    pass
