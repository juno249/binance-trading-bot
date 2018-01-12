#-*- encode: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from trading.models import Coin, Trader

from binance.client import Client


class Command(BaseCommand):

	def handle(self, *args, **options):
		t = Trader.objects.all()[0]
		c = Client(t.api_key, t.secret)

		assets = c.get_all_tickers()
		for asset in assets:
			Coin.objects.get_or_create(symbol=asset['symbol'])
		ei = c.get_exchange_info()

		# Get coin order filters.
		for coin_filter in ei['symbols']:
			symbol = coin_filter['symbol']

			lot_filter = next((item for item in coin_filter['filters'] if item["filterType"] == "LOT_SIZE"), None)

			coin = Coin.objects.get(symbol=symbol)
			coin.max_qty = lot_filter['maxQty']
			coin.min_qty = lot_filter['minQty']
			coin.step_size = lot_filter['stepSize']
			step_split = lot_filter['stepSize'].split(".")

			if step_split[0] == '1':
				coin.step = 0
			else:
				coin.step = len(step_split[1].split("1")[0])+1

			coin.save()