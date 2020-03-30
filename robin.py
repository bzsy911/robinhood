import os
import time
import pandas as pd
import robin_stocks as r
from dotenv import load_dotenv
from utils import close_time, now

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
    all_orders = r.get_all_orders()
    for order in all_orders:
        order['ticker'] = r.get_symbol_by_url(order['instrument'])
    df = pd.DataFrame(all_orders)
    df.to_excel(f'output/order_all.xlsx')
    return
