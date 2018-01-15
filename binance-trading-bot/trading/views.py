from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
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
watched_coins = db.watched_coins
options = db.options
prices = db.prices


@method_decorator(login_required, name='dispatch')
class Dashboard(TemplateView):
    template_name = 'trading/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context['coin_form'] = CoinForm
        context['tradingconditions'] = TradingCondition.objects.all()
        context['trader'] = get_object_or_404(Trader, user=self.request.user)
        return context


@method_decorator(login_required, name='dispatch')
class LogoutView(TemplateView):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGIN_URL)


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
class CoinsAPI(generics.ListAPIView):
    queryset = Coin.objects.all()
    serializer_class = CoinSerializer


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
        c = Client(request.user.trader.api_key, request.user.trader.secret)
        asset = c.get_asset_balance(asset='BTC')
        t = get_object_or_404(Trader, user=request.user) 
        t.btc_balance = asset['free']
        t.save()
        return HttpResponse(asset['free'])
    except BinanceAPIException as e:
        return HttpResponse(e, status=400)


@method_decorator(login_required, name='dispatch')
class CreateOrder(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        try:
            c = Client(request.user.trader.api_key, request.user.trader.secret)
            data = request.data
            btc_to_spend = data['btc-to-spend']
            auto_sell = data['auto-sell']
            stop_loss = data['stop-loss']
            coin_symbol = data['coin']
            coin = get_object_or_404(Coin, symbol=coin_symbol)

            # Calculate quantity to buy. Slice by step.
            btc_price = Decimal(c.get_ticker(symbol=coin_symbol)['askPrice'])

            if coin.step == 0:
                quantity = int(Decimal(btc_to_spend) / btc_price)
            else:
                quantity = '%.{}f'.format(coin.step,) % (Decimal(btc_to_spend) / btc_price)
                step_size = '%.8f' % coin.step_size

            # Check coin order filters.
            if Decimal(quantity) > coin.max_qty:
                return HttpResponse(("Quantity to high! You have tried to order "
                                     "<b>{0} {1}</b>. Maximum quantity is "
                                     "<b>{2}</b>. Step size: {3}")\
                                    .format(quantity, coin.symbol, coin.max_qty,
                                                    step_size), status=400)

            elif Decimal(quantity) < coin.min_qty:
                return HttpResponse(("Quantity to low! You have tried to order "
                                     "<b>{0} {1}</b>. Minimum quantity is "
                                     "<b>{2}</b>. Step size: {3}")\
                                    .format(quantity, coin.symbol, coin.min_qty, 
                                                    step_size), status=400)

            ### PLACE ORDER ###
            order_result = c.create_order(symbol=coin_symbol,
                                          side='BUY',
                                          type='MARKET',
                                          quantity=quantity)

        except BinanceAPIException as e:
            return HttpResponse(e, status=400)

        tc = TradingCondition.objects.create(trader=request.user.trader,
                                             btc_buy_price=btc_price,
                                             auto_sell=auto_sell,
                                             stop_loss=stop_loss,
                                             coin=coin,
                                             quantity=quantity,
                                             btc_amount=btc_to_spend)

        options.find_one_and_update({"option": "watched"}, { '$push': {"coins": {"tc": tc.pk, "s": coin.symbol, "buy": str(btc_price), "stop": stop_loss, "sell": auto_sell}}}, upsert=True)
        return HttpResponse(tc)


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
