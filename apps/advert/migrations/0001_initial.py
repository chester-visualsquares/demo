# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fbid', models.CharField(max_length=32)),
                ('admin_user_id', models.CharField(max_length=32)),
                ('access_token', models.CharField(max_length=256)),
                ('client', models.ForeignKey(to='dashboard.Client')),
            ],
        ),
        migrations.CreateModel(
            name='AdCampaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fbid', models.CharField(max_length=32)),
                ('is_active', models.BooleanField(default=False)),
                ('ad_account', models.ForeignKey(to='advert.AdAccount')),
                ('project', models.OneToOneField(to='dashboard.Project')),
            ],
        ),
    ]
