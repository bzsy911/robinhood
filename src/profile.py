import pandas as pd
from src import api
from src.utils import pct_round


class Profile:

    def __init__(self, ticker):
        self.profile = {'Ticker': ticker}

        if ticker is not None:
            fundamental, price = self.validate()
            if fundamental and price:
                self.build_basic(fundamental, price)
            else:
                self.profile['Delisted'] = True

    def validate(self):
        try:
            fundamental = api.get_fundamentals(self.profile['Ticker'])[0]
            price = api.get_latest_price(self.profile['Ticker'])[0]
        except:
            fundamental = None
            price = None
        return fundamental, price

    def build_basic(self, fundamental, price):
        self.profile.update({'52w_Low': round(float(fundamental['low_52_weeks']), 2),
                             '52w_High': round(float(fundamental['high_52_weeks']), 2),
                             'PE_Ratio': fundamental['pe_ratio'],
                             'Dividend': fundamental['dividend_yield'],
                             'Current_Price': round(float(price), 2)})
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
        buy_in_price = (0.8 - 0.1 * (self.profile['Lock_Depth'] - 1)) * current_avg_cost
        last_bought_at = self.profile['Current_Stack'].iat[-1, 2]
        self.profile.update({'Current_Avg_Cost': round(current_avg_cost, 2),
                             'Buy_in_Price': round(buy_in_price, 2),
                             'Last_Bought_at': round(last_bought_at, 2),
                             'Last_Bought_Change': pct_round(self.profile['Current_Price'] / last_bought_at - 1, 2),
                             'sp15': round(1.15 * last_bought_at, 2),
                             'sp25': round(1.25 * last_bought_at, 2),
                             'sp35': round(1.35 * last_bought_at, 2),
                             'sp50': round(1.5 * last_bought_at, 2)})
        return

    def get_strategy(self):
        if self.profile['Current_Price'] >= self.profile['Last_Bought_at']:
            if 1.03 * self.profile['Current_Price'] < self.profile['sp15']:
                strategy = 'wait'
            elif self.profile['Current_Price'] < self.profile['sp15']:
                strategy = 'watch SELL'
            elif self.profile['Current_Price'] < self.profile['sp50']:
                strategy = 'SELL'
            else:
                strategy = '50%+ SELL'
            gap, target, percent = ([(1 - self.profile['Current_Price'] / target, target, percent/100)
                                     for target, percent in [(self.profile[f'sp{x}'], x) for x in [15, 25, 35, 50]]
                                     if self.profile['Current_Price'] <= target] +
                                    [(0, self.profile['sp50'],
                                      self.profile['Current_Price'] / self.profile['Last_Bought_at'] - 1)])[0]
        else:
            if self.profile['Current_Price'] > self.profile['Buy_in_Price']:
                gap = self.profile['Buy_in_Price'] / self.profile['Current_Price'] - 1
                target = self.profile['Buy_in_Price']
                percent = 0.8 - 0.1 * (self.profile['Lock_Depth'] - 1)
                strategy = 'wait' if 0.97 * self.profile['Current_Price'] >= self.profile['Buy_in_Price'] \
                    else 'watch BUY'
            else:
                gap = 0
                target = self.profile['Buy_in_Price']
                percent = 0.8 - 0.1 * (self.profile['Lock_Depth'] - 1)
                strategy = 'BUY' if self.profile['Current_Price'] >= 0.5 * self.profile['Buy_in_Price'] else '50%- BUY'
        self.profile.update({'Strategy': strategy,
                             'Gap': pct_round(gap, 2),
                             'Next_Target': target,
                             'Next_Target_%': pct_round(percent)})
        sort = gap if 'watch' in strategy else self.profile['Current_Price'] / self.profile['Last_Bought_at'] - 1
        self.profile.update({'Sort': sort})
        return


class Ex(Profile):

    def __init__(self, history):
        self.history = history.sort_values(by='time')
        super().__init__(self.history.iat[0, 1])
        if not self.profile.get('Delisted', False):
            self.build_profile()

    def build_profile(self):
        self.get_recent_trades()
        self.get_limits()
        self.get_strategy()

    def get_recent_trades(self):
        quantity_list = self.history.quantity.tolist()
        partial_sum = [sum(quantity_list[:i+1]) for i in range(len(quantity_list))]
        if partial_sum.count(0) == 1:
            last_trades = self.history
        else:
            clean_up_points = [idx for idx, val in enumerate(partial_sum) if val == 0]
            last_trades = self.history.iloc[clean_up_points[-2] + 1:clean_up_points[-1] + 1, :]
        self.profile.update({'Last_Trades': last_trades,
                             'Total_Prev_Profit': sum(self.history.cost)})
        return

    def get_limits(self):
        last_bought_at = self.profile['Last_Trades'][self.profile['Last_Trades']['quantity'] > 0]['price'].tolist()[-1]
        if last_bought_at == 0:
            self.profile['Gifted'] = True
        last_sold_at = self.profile['Last_Trades'][self.profile['Last_Trades']['quantity'] < 0]['price'].tolist()[-1]
        if not self.profile.get('Gifted', False):
            self.profile.update({'Last_Bought_at': round(last_bought_at, 2),
                                 'Last_Sold_at': round(last_sold_at, 2),
                                 'Position_to_Last_Bought': pct_round(
                                     self.profile['Current_Price'] / last_bought_at),
                                 'Position_to_Last_sold': pct_round(
                                     self.profile['Current_Price'] / last_sold_at),
                                 'Position_to_52w': pct_round(
                                 (self.profile['Current_Price'] - self.profile['52w_Low']) / (
                                     self.profile['52w_High'] - self.profile['52w_Low']))
                                 })
        else:
            self.profile.update({'Last_Bought_at': 0,
                                 'Last_Sold_at': round(last_sold_at, 2),
                                 'Position_to_Last_Bought': None,
                                 'Position_to_Last_sold': pct_round(
                                     self.profile['Current_Price'] / last_sold_at),
                                 'Position_to_52w': pct_round(
                                 (self.profile['Current_Price'] - self.profile['52w_Low']) / (
                                     self.profile['52w_High'] - self.profile['52w_Low']))
                                 })
        return

    def get_strategy(self):
        if self.profile['Current_Price'] < self.profile['Last_Sold_at']:
            target = self.profile['Last_Bought_at']
            if self.profile['Current_Price'] > self.profile['Last_Bought_at']:
                gap = self.profile['Last_Bought_at'] / self.profile['Current_Price'] - 1
                strategy = 'watch BUY'
            else:
                gap = 0
                strategy = 'BUY' if self.profile['Current_Price'] >= 0.8 * self.profile['Last_Bought_at'] \
                    else 'Strong BUY'
        else:
            target = self.profile['Last_Sold_at']
            gap = self.profile['Last_Sold_at'] / self.profile['Current_Price'] - 1
            strategy = 'wait'
        self.profile.update({'Strategy': strategy,
                             'Gap': pct_round(gap, 2),
                             'Next_Target': target})
        if not self.profile.get('Gifted', False):
            sort = gap if 'watch' in strategy else self.profile['Current_Price'] / self.profile['Last_Bought_at'] - 1
        else:
            sort = gap if 'watch' in strategy else self.profile['Current_Price'] / self.profile['Last_Sold_at'] - 1
        self.profile.update({'Sort': sort})

        return


class Prospect(Profile):
    pass


def build_prospects(watch_list):
    pass


if __name__ == '__main__':
    pass
