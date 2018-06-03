# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signup_mobile_tdc_hkjf17', '0004_auto_20170112_0739'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='reminded_idg',
            new_name='reminded_1_idg',
        ),
        migrations.RenameField(
            model_name='contact',
            old_name='reminded_jfs',
            new_name='reminded_1_jfs',
        ),
        migrations.AddField(
            model_name='contact',
            name='reminded_2_idg',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contact',
            name='reminded_2_jfs',
            field=models.BooleanField(default=False),
        ),
    ]
