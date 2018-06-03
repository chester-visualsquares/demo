# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signup_mobile_tdc_hkjf17', '0003_contact_used_fb_mgr'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='aid',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='is_mobile',
            field=models.BooleanField(default=False),
        ),
    ]
