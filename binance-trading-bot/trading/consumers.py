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
    Group("coins").send({"text": message.content['text']})

    for k,v in json.loads(message.content['text']).items():
        if v[0] == 'SOLD':
            tc = TradingCondition.objects.get(pk=k)
            tc.closed = True
            tc.save()