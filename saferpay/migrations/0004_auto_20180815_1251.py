# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-15 12:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('saferpay', '0003_saferpayresponse_status_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saferpaytransaction',
            name='error_code',
        ),
        migrations.RemoveField(
            model_name='saferpaytransaction',
            name='error_message',
        ),
    ]