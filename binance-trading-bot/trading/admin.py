from django.contrib import admin

from trading.models import Coin, TradingCondition, Trader

admin.site.register(Coin)
admin.site.register(TradingCondition)
admin.site.register(Trader)

