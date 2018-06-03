# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0007_auto_20170829_1117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registerreminderlist',
            name='signup',
        ),
        migrations.AddField(
            model_name='event',
            name='signup_info_page_url_str',
            field=models.URLField(default='https://a.wya.me/hktdc/hkjewelleryfair/info-website?fbcsid=FBCSBW9995'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='registerreminderlist',
            name='registered',
            field=models.BooleanField(default=False),
        ),
    ]
