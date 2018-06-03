# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0010_facebookuser_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='gift_message_chi',
            field=models.TextField(max_length=640, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='event',
            name='name_chi',
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name='event',
            name='venue_chi',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
