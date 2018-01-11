from django.contrib import admin
from django.urls import path
from trading.views import Dashboard, LoginView, LogoutView, CoinsAPI, \
                          OpenTradingConditionsAPI, UpdateTraderBalance, \
                          TraderSettings, CreateOrder

urlpatterns = [
  path('', Dashboard.as_view(), name='dashboard'),
  path('api/coin/', CoinsAPI.as_view(), name='coin-api'),
  path('api/tc/open/', OpenTradingConditionsAPI.as_view(), name='open-tc-api'),
  path('api/balance/', UpdateTraderBalance.as_view(), name='trader-balance'),
  path('api/order/', CreateOrder.as_view(), name='create-order'),
  path('settings/', TraderSettings.as_view(), name='trader-settings'),
  path('login/', LoginView.as_view(), name='login'),
  path('logout/', LogoutView.as_view(), name='logout'),
  path('admin/', admin.site.urls),
]
