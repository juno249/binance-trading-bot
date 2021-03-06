#!/usr/bin/env python3

import os
import time
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_core.settings')

import datetime
from decimal import Decimal
from django.conf import settings
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.exceptions import BinanceAPIException
from pymongo import MongoClient

from _core.asgi import channel_layer


client = MongoClient()
db = client['binance']
prices = db.prices
watched = db.watched
binance_client = Client(settings.BINANCE_API_KEY, settings.BINANCE_SECRET)


while True:
    payload = {}
    for coin_watched in watched.find():
        current_price = prices.find_one({"s": coin_watched['s']})['c']
        buy_price = Decimal(coin_watched['buy'])
        change = round((Decimal(current_price) - buy_price) / buy_price \
                                                                * 100, 2)
        if change >= int(coin_watched['sell']) or \
           change <= -int(coin_watched['stop']):

            watched.delete_one({"tc": coin_watched['tc']})
            payload[int(coin_watched['tc'])] = ["SOLD", str(change)]

            try:
                o_r = binance_client.create_order(symbol=coin_watched['s'],
                                                  side='SELL',
                                                  type='MARKET',
                                                  quantity=coin_watched['q'])
                print(o_r)

            except BinanceAPIException as e:
                print(binance_client.get_account())
                print(e, coin_watched)
        else:
            payload[int(coin_watched['tc'])] = [current_price, str(change)]

    channel_layer.send("prices", {"text": json.dumps(payload)})
    time.sleep(0.5)