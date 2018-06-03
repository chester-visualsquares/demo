# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_project_cs_daily_sync_required'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('aid', models.CharField(max_length=16)),
                ('network', models.CharField(default=b'FB', max_length=2, choices=[('FB', 'Facebook'), ('WE', 'Wechat')])),
                ('language', models.CharField(default=b'CHI', max_length=4, choices=[('CHI', 'Chinese'), ('ENG', 'English'), ('SC', 'Smplified_Chinese')])),
                ('short_url', models.URLField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='url_str',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='aid_pattern',
            field=models.CharField(max_length=32),
        ),
        migrations.AddField(
            model_name='channel',
            name='project',
            field=models.ForeignKey(to='dashboard.Project'),
        ),
    ]
