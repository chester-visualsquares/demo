# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signup_mobile_tdc_hkjf17', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='auth_str',
            field=models.CharField(default=None, unique=True, max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='is_show_mgr_btn',
            field=models.BooleanField(default=False),
        ),
    ]
