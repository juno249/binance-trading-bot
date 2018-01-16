#!/usr/bin/env python3

import os
import datetime
from django.conf import settings
from binance.client import Client
from binance.websockets import BinanceSocketManager

from pymongo import MongoClient

client = MongoClient()
db = client['binance']
prices = db.prices

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_core.settings')

c = Client(settings.BINANCE_API_KEY, settings.BINANCE_SECRET)

def process_message(payload):
	for coin in payload:
		prices.find_one_and_update({"s": coin['s']}, {"$set": {"c": str(coin['c'])}}, upsert=True)
	print("[{}] Prices added.".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

bm = BinanceSocketManager(c)
bm.start_ticker_socket(process_message)
bm.start()
