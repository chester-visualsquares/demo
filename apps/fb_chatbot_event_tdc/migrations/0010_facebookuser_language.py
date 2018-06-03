# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0009_remove_event_reminder_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebookuser',
            name='language',
            field=models.CharField(default=b'eng', max_length=8),
        ),
    ]
