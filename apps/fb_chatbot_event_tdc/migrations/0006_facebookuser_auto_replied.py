# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0005_auto_20170116_1930'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebookuser',
            name='auto_replied',
            field=models.BooleanField(default=False),
        ),
    ]
