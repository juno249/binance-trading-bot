import json
import datetime
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.websockets import BinanceSocketManager

from .models import Coin, TradingCondition, Trader
from .forms import CoinForm, TraderSettingsForm
from .serializers import CoinSerializer, TradingConditionSerializer

from pymongo import MongoClient


client = MongoClient()
db = client['binance']
watched = db.watched
prices = db.prices
binance_client = Client(settings.BINANCE_API_KEY, settings.BINANCE_SECRET)


@method_decorator(login_required, name='dispatch')
class Dashboard(TemplateView):
    template_name = 'trading/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context['coin_form'] = CoinForm
        context['tradingconditions'] = TradingCondition.objects.all()
        context['trader'] = get_object_or_404(Trader, user=self.request.user)
        return context


class LoginView(TemplateView):
    template_name = "trading/login.html"
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/')

        if user is None or not user.is_active:
            return HttpResponseRedirect("{}?invalid=1".format(reverse_lazy('login'),))


@method_decorator(login_required, name='dispatch')
class LogoutView(TemplateView):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGIN_URL)


@method_decorator(login_required, name='dispatch')
class CoinsAPI(generics.ListAPIView):
    serializer_class = CoinSerializer

    def get_queryset(self):
        queryset = Coin.objects.all()
        market = self.request.query_params.get('market', None)
        if market is not None:
            queryset = queryset.filter(symbol__endswith=market)
        return queryset


@method_decorator(login_required, name='dispatch')
class OpenTradingConditionsAPI(generics.ListAPIView):
    serializer_class = TradingConditionSerializer

    def get_queryset(self):
        return TradingCondition.objects.filter(trader=self.request.user.trader, closed=False)


@method_decorator(login_required, name='dispatch')
class UpdateTraderBalance(APIView):
   permission_classes = (IsAuthenticated,)
   def get(self, request, format=None):
    try:
        c = binance_client
        asset_btc = c.get_asset_balance(asset='BTC')
        asset_eth = c.get_asset_balance(asset='ETH')
        t = get_object_or_404(Trader, user=request.user) 
        t.btc_balance = asset_btc['free']
        t.eth_balance = asset_eth['free']
        t.save()
        return HttpResponse(json.dumps({"BTC": asset_btc['free'], "ETH": asset_eth['free']}))
    except BinanceAPIException as e:
        return HttpResponse(e, status=400)
    except Trader.DoesNotExist:
        raise Http404


@method_decorator(login_required, name='dispatch')
class CreateOrder(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        seconds = 0
        start_time = datetime.datetime.now()
        try:
            data = request.data
            btc_to_spend = Decimal(data['amount-to-spend'])
            auto_sell = data['auto-sell']
            stop_loss = data['stop-loss']
            coin_symbol = data['coin']
            coin = get_object_or_404(Coin, symbol=coin_symbol)
            btc_price = Decimal(prices.find_one({"s": coin_symbol})['c'])

            # Set coin step
            if coin.step == 0:
                quantity = int(btc_to_spend / btc_price)
            else:
                quantity = Decimal('%.{}f'.format(coin.step,) % (btc_to_spend / btc_price))

            print("Order: {} :: {} @ {}".format(coin_symbol, quantity, btc_price))

            # Too much coins to buy!
            if quantity > coin.max_qty:
                return HttpResponse(("Quantity to high! You have tried to order "
                                     "<b>{0} {1}</b>. Maximum quantity is "
                                     "<b>{2}</b>. Step size: {3}")\
                                    .format(quantity, coin.symbol, coin.max_qty,
                                                    '%.8f' % coin.step_size), status=400)
            # Too little coins to buy!
            elif quantity < coin.min_qty:
                return HttpResponse(("Quantity to low! You have tried to order "
                                     "<b>{0} {1}</b>. Minimum quantity is "
                                     "<b>{2}</b>. Step size: {3}")\
                                    .format(quantity, coin.symbol, coin.min_qty, 
                                                    '%.8f' % coin.step_size), status=400)

            ### PLACE ORDER ###
            order_result = binance_client.create_order(symbol=coin_symbol,
                                          side='BUY',
                                          type='MARKET',
                                          quantity=quantity)
            print(order_result)

            # Check asset quantity.
            try:
                quantity = binance_client.get_asset_balance(
                        asset='{}'.format(coin_symbol.replace('BTC', '').replace('ETH', '')))['free']
            except Exception as e:
                print(e)

            tc = TradingCondition.objects.create(trader=request.user.trader,
                                                 btc_buy_price=btc_price,
                                                 auto_sell=auto_sell,
                                                 stop_loss=stop_loss,
                                                 coin=coin,
                                                 quantity=quantity,
                                                 btc_amount=btc_to_spend)

            # Insert order into watched collection
            watched.insert({"tc": tc.pk, "s": coin.symbol, "q": str(quantity), "buy": str(btc_price), 
                                    "stop": stop_loss, "sell": auto_sell, "change": 0.00})

        except BinanceAPIException as e:
            return HttpResponse(e, status=400)

        else:
            # Calculate order time
            seconds = (datetime.datetime.now()-start_time).total_seconds()
            return HttpResponse(seconds)


@method_decorator(login_required, name='dispatch')
class TraderSettings(TemplateView):
    template_name = 'trading/settings.html'

    def get_context_data(self, **kwargs):
        context = super(TraderSettings, self).get_context_data(**kwargs)
        trader = get_object_or_404(Trader, user=self.request.user)
        context['settings_form'] = TraderSettingsForm(initial={'api_key': trader.api_key, 'secret': trader.secret})
        return context

    def post(self, request):
        api_key = request.POST.get('api_key')
        secret = request.POST.get('secret')
        trader = get_object_or_404(Trader, user=request.user)
        trader.api_key = api_key
        trader.secret = secret
        trader.save()
        return HttpResponseRedirect(reverse_lazy('trader-settings'))
