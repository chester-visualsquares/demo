# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('timezone', models.CharField(default=b'Asia/Hong_Kong', max_length=32, choices=[('Asia/Hong_Kong', 'Asia/Hong_Kong (GMT +08:00)'), ('Etc/UTC', 'Etc/UTC (GMT +00:00)')])),
                ('daily_report_required', models.BooleanField(default=True)),
                ('country_breakdown_required', models.BooleanField(default=True)),
                ('signup_list_required', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='DailyAdStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('impressions', models.PositiveIntegerField()),
                ('clicks', models.PositiveIntegerField()),
                ('link_clicks', models.PositiveIntegerField(null=True)),
                ('spent', models.PositiveIntegerField()),
                ('conversions', models.PositiveIntegerField()),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('network', models.CharField(default=b'FB', max_length=16, choices=[('FB', 'Facebook'), ('LN', 'LinkedIn'), ('TW', 'Twitter')])),
                ('model_path', models.CharField(max_length=128, blank=True)),
                ('queryset_filters', models.CharField(default=b'{}', max_length=64, blank=True)),
                ('country_field_name', models.CharField(max_length=32, blank=True)),
                ('cs_id', models.CharField(max_length=16, blank=True)),
                ('gid_pattern', models.CharField(max_length=32, blank=True)),
                ('aid_pattern', models.CharField(max_length=32, blank=True)),
                ('unique_by', models.CharField(default=None, max_length=32, blank=True)),
                ('attribution_window', models.IntegerField(default=None, null=True, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('last_update', models.DateTimeField()),
                ('client', models.ForeignKey(to='dashboard.Client')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timezone', models.CharField(default=b'Asia/Hong_Kong', max_length=32, choices=[('Asia/Hong_Kong', 'Asia/Hong_Kong (GMT +08:00)'), ('Etc/UTC', 'Etc/UTC (GMT +00:00)')])),
                ('client', models.ForeignKey(blank=True, to='dashboard.Client', null=True)),
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='dailyadstats',
            name='project',
            field=models.ForeignKey(to='dashboard.Project'),
        ),
        migrations.AlterUniqueTogether(
            name='dailyadstats',
            unique_together=set([('project', 'date')]),
        ),
    ]
