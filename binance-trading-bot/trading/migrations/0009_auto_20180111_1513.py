# Generated by Django 2.0.1 on 2018-01-11 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0008_auto_20180111_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tradingcondition',
            name='change',
            field=models.IntegerField(default=0),
        ),
    ]
