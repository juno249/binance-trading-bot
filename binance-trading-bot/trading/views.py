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

from .models import Coin, TradingCondition, Trader
from .forms import CoinForm, TraderSettingsForm
from .serializers import CoinSerializer, TradingConditionSerializer


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
    queryset = TradingCondition.objects.filter(closed=False)
    serializer_class = TradingConditionSerializer


@method_decorator(login_required, name='dispatch')
class UpdateTraderBalance(APIView):
   permission_classes = (IsAuthenticated,)
   def get(self, request, format=None):
        c = Client(request.user.trader.api_key, request.user.trader.secret)
        asset = c.get_asset_balance(asset='BTC')
        t = get_object_or_404(Trader, user=request.user) 
        t.btc_balance = asset['free']
        t.save()
        return HttpResponse(asset['free'])


@method_decorator(login_required, name='dispatch')
class CreateOrder(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        c = Client(request.user.trader.api_key, request.user.trader.secret)
        data = request.data
        btc_to_spend = data['btc-to-spend']
        auto_sell = data['auto-sell']
        stop_loss = data['stop-loss']
        coin_symbol = data['coin']
        coin = get_object_or_404(Coin, symbol=coin_symbol)
        bid_price = c.get_ticker(symbol=coin.symbol)['bidPrice']

        print(coin.btc_price, Decimal(bid_price))

        # Update coin price.
        if coin.btc_price != Decimal(bid_price):
            coin.btc_price = Decimal(bid_price)
            coin.save()

        # Calculate quantity to buy. Slice by step
        quantity = '%.{}f'.format(coin.step,) % (Decimal(btc_to_spend) / coin.btc_price)
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

        try:
            order_result = c.create_order(symbol=coin_symbol,
                                          side='BUY',
                                          type='MARKET',
                                          quantity=quantity)
            print(order_result)

        except BinanceAPIException as e:
            return HttpResponse(e, status=400)

        tc = TradingCondition.objects.create(trader=request.user.trader,
                                             btc_buy_price=coin.btc_price,
                                             auto_sell=auto_sell,
                                             stop_loss=stop_loss,
                                             coin=coin,
                                             quantity=quantity,
                                             btc_amount=btc_to_spend)

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