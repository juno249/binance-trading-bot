# Generated by Django 2.0.1 on 2018-01-11 19:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0017_auto_20180111_1916'),
    ]

    operations = [
        migrations.AddField(
            model_name='tradingcondition',
            name='btc_amount',
            field=models.DecimalField(decimal_places=8, default=1e-06, max_digits=20),
            preserve_default=False,
        ),
    ]
