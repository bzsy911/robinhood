import os
import time
import pandas as pd
import robin_stocks as r
from dotenv import load_dotenv
load_dotenv()
login = r.login(os.getenv('EMAIL'), os.getenv('PASSWORD'))


def close_time(extend=False):
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 18 if extend else 16, 0, 0, t.tm_wday, t.tm_yday, t.tm_isdst))


market_close = close_time()
extend_close = close_time(True)

stocks = list(r.build_holdings().keys())
data = [stocks+['Time']]

start = time.strftime("%b %d %Y, %H:%M:%S", time.localtime())
print('Data Recording Starts at:', start)
print('Scheduled Close Time at:', time.strftime("%b %d %Y, %H:%M:%S", time.localtime(market_close)))

count = 0
while time.time() < market_close:
    count += 1
    prices = r.stocks.get_latest_price(stocks)
    print(time.strftime("%H:%M:%S", time.localtime()), [s+": "+str(round(float(x), 2)) for s, x in zip(stocks, prices)])
    data.append(prices + [time.localtime()])
    if count % 100 == 0:
        df = pd.DataFrame(data)
        curr = time.strftime("%b_%d_%Y_%H_%M_%S", time.localtime())
        df.to_excel(f'output/price_{start}_{curr}.xlsx')
    time.sleep(5)

end = time.strftime("%b_%d_%Y_%H_%M_%S", time.localtime())
df = pd.DataFrame(data)
df.to_excel(f'output/price_{start}_{end}.xlsx')
print('data saved')
