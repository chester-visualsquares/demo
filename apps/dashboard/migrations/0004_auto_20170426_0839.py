# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_auto_20170310_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='language',
            field=models.CharField(default=b'CHI', max_length=4, choices=[('CHI', 'Chinese'), ('ENG', 'English'), ('SC', 'Simplified Chinese')]),
        ),
    ]
