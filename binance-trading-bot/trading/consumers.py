import json
from decimal import Decimal
from channels import Group
from pymongo import MongoClient
from trading.models import TradingCondition
from binance.client import Client


client = MongoClient()
db = client['binance']
prices = db.prices
options = db.options


def ws_add(message):
    message.reply_channel.send({"accept": True})
    Group("coins").add(message.reply_channel)


def ws_disconnect(message):
    channel = dict(message.items())['reply_channel']
    Group("coins").discard(message.reply_channel)


def ws_message(message):
    channel = dict(message.items())['reply_channel']
    msg_text = message.content['text']


def ws_prices(message):
    payload = {}
    d = json.loads(message.content['text'])
    watched_coins = options.find_one({"option": "watched"})['coins']
    for coin in watched_coins:
        tc = TradingCondition.objects.get(pk=int(coin['tc']))
        try:
            c = next((item for item in d if item["s"] == coin['s']))
            prices.find_one_and_update({"coin": c['s']}, {"$set": {"p": str(c['c'])}}, upsert=True)
            current_price = Decimal(c['c'])
            buy_price = Decimal(coin['buy'])
            change = round((current_price - buy_price) / buy_price * 100, 2)
            if change <= -int(coin['stop']) or change >= int(coin['sell']):
                client = Client(tc.trader.api_key, tc.trader.secret)
                order_result = client.create_order(symbol=coin['s'],
                                                        side='SELL',
                                                        type='MARKET',
                                                        quantity=tc.quantity)
                print(order_result)
                tc.closed = True
                tc.save()
                options.find_one_and_update({"option": "watched"}, { "$pull": {"coins": {"s": coin['s']}}})

            payload[c['s']] = {"p": str(c['c']), "change": str(change)}

        except StopIteration:
            pass

    Group("coins").send({"text": json.dumps(payload)})