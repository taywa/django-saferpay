# Generated by Django 2.2.12 on 2020-06-27 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saferpay', '0007_auto_20180911_2207'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saferpaytransaction',
            name='order_id',
            field=models.CharField(max_length=64),
        ),
    ]
