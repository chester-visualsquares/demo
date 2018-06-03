# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdCampaignSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('cpa_target_1', models.PositiveIntegerField()),
                ('cpa_target_2', models.PositiveIntegerField()),
                ('budget', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('client', models.ForeignKey(to='dashboard.Client')),
                ('project', models.OneToOneField(to='dashboard.Project')),
            ],
        ),
    ]
