# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0008_auto_20170903_1317'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='reminder_messages',
        ),
    ]
