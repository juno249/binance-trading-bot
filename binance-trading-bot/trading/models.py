from django.db import models
from django.contrib.auth.models import User


class Trader(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	api_key = models.CharField(max_length=64)
	secret = models.CharField(max_length=64)
	btc_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)

	def __unicode__(self):
		return self.user.username


class Coin(models.Model):
	btc_price = models.DecimalField(max_digits=20, decimal_places=8)
	symbol = models.CharField(primary_key=True, unique=True, max_length=10)
	max_qty = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)
	min_qty = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)
	step_size = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000001)
	step = models.IntegerField(default=8)

	def __unicode__(self):
		return self.symbol


class TradingCondition(models.Model):
	trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
	time_created = models.DateTimeField(auto_now_add=True)
	auto_sell = models.PositiveIntegerField(default=0)
	stop_loss = models.PositiveIntegerField(default=0)
	coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
	btc_buy_price = models.DecimalField(max_digits=20, decimal_places=8)
	change = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
	closed = models.BooleanField(default=False)
	btc_amount = models.DecimalField(max_digits=20, decimal_places=8)
	earnings = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
	quantity = models.DecimalField(max_digits=20, decimal_places=8)

	@property
	def current_price(self):
		return self.coin.btc_price
