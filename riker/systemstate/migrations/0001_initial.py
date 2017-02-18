# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 13:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CecConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_address', models.PositiveIntegerField()),
                ('target_address', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Command',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command_type', models.CharField(max_length=255)),
                ('data', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CommandSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition_type', models.CharField(choices=[('any', 'Any'), ('all', 'All')], max_length=3)),
                ('nested_conditions', models.ManyToManyField(blank=True, null=True, related_name='_condition_nested_conditions_+', to='systemstate.Condition')),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('cec_config', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='systemstate.CecConfig')),
            ],
        ),
        migrations.CreateModel(
            name='IrsendConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remote_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='RemoteButton',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lirc_code', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='SerialConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port_name', models.CharField(max_length=255)),
                ('baud_rate', models.PositiveIntegerField()),
                ('byte_size', models.PositiveIntegerField()),
                ('timeout', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='StateSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='state_sets', to='systemstate.Device')),
                ('status', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='systemstate.State')),
            ],
        ),
        migrations.CreateModel(
            name='StateSideEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('commands', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='side_effects', to='systemstate.CommandSet')),
                ('states', models.ManyToManyField(related_name='reachable_by', to='systemstate.State')),
            ],
        ),
        migrations.CreateModel(
            name='TcpConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host', models.CharField(max_length=255)),
                ('port', models.PositiveIntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='state',
            name='state_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='systemstate.StateSet'),
        ),
        migrations.AddField(
            model_name='device',
            name='irsend_config',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='systemstate.IrsendConfig'),
        ),
        migrations.AddField(
            model_name='device',
            name='serial_config',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='systemstate.SerialConfig'),
        ),
        migrations.AddField(
            model_name='device',
            name='tcp_config',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='systemstate.TcpConfig'),
        ),
        migrations.AddField(
            model_name='condition',
            name='states',
            field=models.ManyToManyField(blank=True, null=True, related_name='_condition_states_+', to='systemstate.State'),
        ),
        migrations.AddField(
            model_name='commandset',
            name='condition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='systemstate.Condition'),
        ),
        migrations.AddField(
            model_name='commandset',
            name='trigger',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='macros', to='systemstate.RemoteButton'),
        ),
        migrations.AddField(
            model_name='command',
            name='condition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='systemstate.Condition'),
        ),
        migrations.AddField(
            model_name='command',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commands', to='systemstate.Device'),
        ),
        migrations.AddField(
            model_name='command',
            name='trigger',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commands', to='systemstate.CommandSet'),
        ),
    ]
