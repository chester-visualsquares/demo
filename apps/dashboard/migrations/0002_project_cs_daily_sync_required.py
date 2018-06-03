# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='cs_daily_sync_required',
            field=models.BooleanField(default=False),
        ),
    ]
