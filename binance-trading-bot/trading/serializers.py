from rest_framework import serializers
from .models import *


class CoinSerializer(serializers.ModelSerializer):
	text = serializers.CharField(source='pk')
	value = serializers.CharField(source='pk')

	class Meta:
		model = Coin
		fields = ('text','value')


class TradingConditionSerializer(serializers.ModelSerializer):
	price = serializers.StringRelatedField(source='current_price')
	
	class Meta:
		model = TradingCondition
		fields = ['btc_amount', 'quantity', 'auto_sell', 'stop_loss', 'coin', 'btc_buy_price',
				  'change', 'closed', 'earnings', 'price', 'time_created']