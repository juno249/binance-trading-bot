# Generated by Django 2.0.1 on 2018-01-11 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0011_trader'),
    ]

    operations = [
        migrations.AddField(
            model_name='trader',
            name='btc_balance',
            field=models.DecimalField(decimal_places=8, default=0.0, max_digits=20),
        ),
    ]
