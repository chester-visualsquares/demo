# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signup_mobile_tdc_hkjf17', '0002_auto_20170108_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='used_fb_mgr',
            field=models.BooleanField(default=False),
        ),
    ]
