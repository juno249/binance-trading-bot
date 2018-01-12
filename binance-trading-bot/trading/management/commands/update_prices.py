#-*- encode: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from trading.models import Coin, TradingCondition, Trader

from binance.client import Client


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Price updates!")
        t = Trader.objects.all()[0]
        c = Client(t.api_key, t.secret)
        assets = c.get_all_tickers()
        for asset in assets:
            coin, crt = Coin.objects.get_or_create(symbol=asset['symbol'])
            coin.btc_price = asset['price']
            coin.save()

            trading_orders = TradingCondition.objects.filter(closed=False, coin=coin)
            for tc in trading_orders:

                # Calculate price change in percentage. IF AutoSell or StopLoss
                # is triggered - sell coins.

                change = round((tc.coin.btc_price - tc.btc_buy_price) / tc.btc_buy_price * 100, 2)
                tc.change = change

                if change >= tc.auto_sell:
                    # Send market SELL order
                    print("AUTO SELL!", coin.symbol, tc.btc_buy_price, tc.coin.btc_price, change)
                    c = Client(tc.trader.api_key, tc.trader.secret)
                    order_result = c.create_order(symbol=coin.symbol,
                                                  side='SELL',
                                                  type='MARKET',
                                                  quantity=tc.quantity)
                    print(order_result)
                    tc.closed = True

                elif change <= -tc.stop_loss:
                    # Send market SELL order
                    print("STOP LOSS!", coin.symbol, tc.btc_buy_price, tc.coin.btc_price, change)
                    c = Client(tc.trader.api_key, tc.trader.secret)
                    order_result = c.create_order(symbol=coin.symbol,
                                                  side='SELL',
                                                  type='MARKET',
                                                  quantity=tc.quantity)
                    print(order_result)
                    tc.closed = True

                tc.save()

        print("Prices updated!")