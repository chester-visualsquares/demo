# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_auto_20170426_0839'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='url_str',
        ),
        migrations.AddField(
            model_name='project',
            name='cn_url',
            field=models.URLField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='non_cn_url_chi',
            field=models.URLField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='non_cn_url_eng',
            field=models.URLField(max_length=128, blank=True),
        ),
        migrations.AlterField(
            model_name='channel',
            name='network',
            field=models.CharField(default=b'FB', max_length=2, choices=[('FB', 'Non-China'), ('WE', 'China')]),
        ),
    ]
