# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-28 04:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0007_auto_20190131_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='targetlanguage',
            name='notes',
            field=models.CharField(max_length=64, null=True),
        ),
    ]