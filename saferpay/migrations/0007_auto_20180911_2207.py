# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-09-11 22:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saferpay', '0006_saferpaytransaction_notify_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saferpaytransaction',
            name='notify_token',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
