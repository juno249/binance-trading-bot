# Generated by Django 2.0.1 on 2018-01-11 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0015_auto_20180111_1838'),
    ]

    operations = [
        migrations.AddField(
            model_name='tradingcondition',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True),
        ),
    ]
