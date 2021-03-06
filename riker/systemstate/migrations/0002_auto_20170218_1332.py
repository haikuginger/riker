# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 13:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('systemstate', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='condition',
            name='nested_conditions',
            field=models.ManyToManyField(blank=True, related_name='_condition_nested_conditions_+', to='systemstate.Condition'),
        ),
        migrations.AlterField(
            model_name='condition',
            name='states',
            field=models.ManyToManyField(blank=True, related_name='_condition_states_+', to='systemstate.State'),
        ),
    ]
