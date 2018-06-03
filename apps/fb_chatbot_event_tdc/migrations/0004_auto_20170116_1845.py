# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0003_facebookpage'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveredmessage',
            name='fb_page',
            field=models.ForeignKey(default=1, to='fb_chatbot_event_tdc.FacebookPage'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='deliverypostback',
            name='fb_page',
            field=models.ForeignKey(default=1, to='fb_chatbot_event_tdc.FacebookPage'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='fb_page',
            field=models.ForeignKey(default=1, to='fb_chatbot_event_tdc.FacebookPage'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='facebookuser',
            name='fb_page',
            field=models.ForeignKey(default=1, to='fb_chatbot_event_tdc.FacebookPage'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='receivedmessage',
            name='fb_page',
            field=models.ForeignKey(default=1, to='fb_chatbot_event_tdc.FacebookPage'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='receivedpostback',
            name='fb_page',
            field=models.ForeignKey(default=1, to='fb_chatbot_event_tdc.FacebookPage'),
            preserve_default=False,
        ),
    ]
