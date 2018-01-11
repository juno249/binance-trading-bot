# Generated by Django 2.0.1 on 2018-01-11 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0012_trader_btc_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='coin',
            name='max_qty',
            field=models.DecimalField(decimal_places=8, default=0.0, max_digits=20),
        ),
        migrations.AddField(
            model_name='coin',
            name='min_qty',
            field=models.DecimalField(decimal_places=8, default=0.0, max_digits=20),
        ),
        migrations.AddField(
            model_name='coin',
            name='step_size',
            field=models.DecimalField(decimal_places=8, default=0.0, max_digits=20),
        ),
    ]
