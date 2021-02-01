import src.api as api
from src.order import process_raw_history
from src.profile import Present
import pandas as pd
pd.options.mode.chained_assignment = None

"""
Questions:
    1. For holdings:
        Should I buy?
            - Yes if the latest price is lower than some value
        Should I sell?
            - Yes if the latest price is higher than some value
    2. For other stocks:
        Should I buy?
            Is there any dividend?
            What is the average volume? > 25MM?
            How is the latest price sit in between 52w high and 52w low
            Is the latest price lower than the fair value
        For ex:
            Is the latest price lower than the last sell price?
            Is the latest price comparable to the last buy price?


Pipeline:
    1. Get holding and ex information
        a. Login
        b. get order history
        c. analysis history to get holding and ex
        d. build strategy profile for holding
    
    2. Get new logo information
        a. get watch list.
        b. get latest price, 52w high, 52w low, dividend, volume for ex and new logo
        c. get fair value for morning star for ex and new logo    
    
    3. Check if any buy or sell opportunity exists
        a. keep most info in memory
        b. request latest price every x minutes
        c. rebuild memory after new transaction is made
"""


def build_holding_strategy(from_csv=True):
    if from_csv:
        order_df = pd.read_csv('output/order_all.csv')
    else:
        order_df = process_raw_history(api.get_all_stock_orders())
    tb = order_df.groupby('ticker')[['quantity']].sum()
    portfolio = [Present(order_df[order_df['ticker'] == ticker]) for ticker in tb[tb['quantity'] != 0].index]
    for profile in portfolio:
        print(profile.strategy)


if __name__ == "__main__":
    build_holding_strategy()
