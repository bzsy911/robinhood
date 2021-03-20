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


def build_holding_strategy(extract_new_orders=False, write_to_file=False):
    if extract_new_orders:
        order_df = process_raw_history(api.get_all_stock_orders())
    else:
        order_df = pd.read_csv('output/order_all.csv')
    tb = order_df.groupby('ticker')[['quantity']].sum()
    portfolio = [Present(order_df[order_df['ticker'] == ticker]) for ticker in tb[tb['quantity'] != 0].index]
    present = pd.DataFrame([p.profile for p in portfolio])
    if write_to_file:
        present.to_excel('output/present_strategy.xlsx', index=False)

    lite_col = ['Ticker', 'Holding', 'Last_Bought_at', 'Lock_Depth', 'Last_Bought_Change', 'Current_Price',
                'Next_Target', 'Next_Target_%', 'Gap']
    sell = present[present['Strategy'].isin(['SELL', '50%+ SELL'])].sort_values('Sort', ascending=False)[lite_col]
    buy = present[present['Strategy'].isin(['BUY', '50%- BUY'])].sort_values('Sort')[lite_col]
    high = present[present['Strategy'] == 'watch SELL'].sort_values('Sort')[lite_col]
    low = present[present['Strategy'] == 'watch BUY'].sort_values('Sort', ascending=False)[lite_col]
    keep = present[present['Strategy'] == 'wait'].sort_values('Sort', ascending=False)[lite_col]

    pd.set_option("display.max_rows", None,
                  "display.max_columns", None,
                  "display.width", 150)
    ls = list(zip([sell, buy, high, low, keep],
                  ['Ready to Sell:', 'Ready to Buy:', 'Close to Sell:', 'Close to Buy:', 'Keep Waiting:']))
    for i in range(5):
        # set 5 if want to print Keeps
        df, title = ls[i]
        if len(df) > 0:
            print(title)
            print(df)
            print()
    return


if __name__ == "__main__":
    build_holding_strategy(extract_new_orders=True, write_to_file=True)
    # build_holding_strategy()