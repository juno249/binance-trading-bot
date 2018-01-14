#!/usr/bin/env python3

import os, time, datetime, json
from django.conf import settings
from binance.client import Client
from binance.websockets import BinanceSocketManager
from channels import Group
from _core.asgi import channel_layer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_core.settings')

c = Client(settings.BINANCE_API_KEY, settings.BINANCE_SECRET)

def process_message(payload):
    channel_layer.send("prices", {"text": json.dumps(payload)})

bm = BinanceSocketManager(c)
bm.start_ticker_socket(process_message)
bm.start()
print("Websocket prices updates.")