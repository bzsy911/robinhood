import pandas as pd
import matplotlib.pyplot as plt

data = "output/price_Mar 27 2020 10:00:09_Mar 27 2020 11:57:34.xlsx"
df = pd.read_excel(data)

dt = {}
for i in range(18):
    dt[df[i][0]] = [float(x) for x in df[i][1:]]


def trade(obs, thresh=1):
    holding = 0
    money = 10000
    hist = [10000]
    prev = obs[0]

    for i in obs[1:]:
        # print(i, end=' ')
        if holding == 0:
            if i > prev * thresh:
                holding, money = divmod(money, i)
                # print(f'buy {holding} shares, money left: {money}', end='')
        else:
            if i < prev * thresh:
                money += i * holding
                holding = 0
                # print(f'sell all shares, money left: {money}', end='')
        prev = i
        # print()
        hist.append(money + holding * i)
    if holding > 0:
        money += prev * holding
        # print(f'market close. Sell all shares, money left: {money}')

    plt.subplot(2,1,1)
    plt.plot(hist)
    plt.grid()

    plt.subplot(2,1,2)
    plt.plot(obs)
    plt.grid()
    plt.show()

    return money - 10000


# res = [(cusip, round(trade(price), 2)) for cusip, price in dt.items()]
# for c, r in res:
#     print(c, r)
# print()
# print('total', sum([r for _, r in res]))
for k in dt:
    print(k)
    trade(dt[k])
