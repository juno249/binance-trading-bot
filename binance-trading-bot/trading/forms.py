from django import forms
from .models import TradingCondition

single_ac_attrs = {"class": "singleinputautocomplete"}


class CoinForm(forms.ModelForm):

	coin = forms.CharField(required=True, widget=forms.TextInput(attrs=single_ac_attrs))

	class Meta:
		model = TradingCondition
		fields = ['coin',]


class TraderSettingsForm(forms.Form):
	api_key = forms.CharField(required=True)
	secret = forms.CharField(required=True)
