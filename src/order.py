import pandas as pd
import json
from src import api


def process_raw_history(all_orders):
    with open('data/reference/ticker_dict.json') as f:
        ticker_dict = json.load(f)
    with open('data/reference/ticker_map.json') as f:
        ticker_map = json.load(f)
    with open('data/reference/split_history.csv') as f:
        split_history = [line.split(',') for line in f.readlines()]

    all_orders = [order for order in all_orders if float(order['cumulative_quantity']) != 0]
    for order in all_orders:
        order['amount'] = -1 * float(order['executed_notional']['amount'])
        order['quantity'] = float(order['cumulative_quantity'])
        if order['side'] == 'sell':
            order['amount'] *= -1
            order['quantity'] *= -1
        order['fees'] = -1 * float(order['fees'])
        order['time'] = order['last_transaction_at'].replace('T', ' ')[:19]
        order['price'] = float(order['average_price'])
        order['cost'] = order['amount'] + order['fees']
        if order['instrument'] not in ticker_dict:
            order['ticker'] = api.get_symbol_by_url(order['instrument'])
            ticker_dict[order['instrument']] = order['ticker']
        else:
            order['ticker'] = ticker_dict[order['instrument']]

    for order in all_orders:
        order['ticker'] = ticker_map.get(order['ticker'], order['ticker'])

    all_orders.extend([{'time': time, 'ticker': ticker, 'price': float(price),
                        'quantity': float(quantity), 'cost': float(cost), 'instrument': ''}
                       for time, ticker, price, quantity, cost in split_history])

    df = pd.DataFrame(all_orders)[['time', 'ticker', 'price', 'quantity', 'cost']]
    df.to_csv(f'output/order_all.csv', index=False)

    with open('data/reference/ticker_dict.json', 'w') as f:
        json.dump(ticker_dict, f)

    return df


if __name__ == '__main__':
    process_raw_history(api.get_all_stock_orders())
