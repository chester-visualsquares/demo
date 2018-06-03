# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0004_auto_20170116_1845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facebookuser',
            name='fbid',
            field=models.BigIntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='facebookuser',
            unique_together=set([('fb_page', 'fbid')]),
        ),
    ]
