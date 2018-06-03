# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import common.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=128)),
                ('last_name', models.CharField(max_length=128)),
                ('company', models.CharField(max_length=128)),
                ('email', models.EmailField(max_length=256)),
                ('country_code', models.IntegerField()),
                ('mobile_phone', common.models.PhoneNumberField(max_length=16)),
                ('attend_jfs', models.BooleanField(default=True)),
                ('attend_idg', models.BooleanField(default=True)),
                ('signup_code_jfs', models.CharField(default=None, max_length=64, unique=True, null=True, blank=True)),
                ('signup_code_idg', models.CharField(default=None, max_length=64, unique=True, null=True, blank=True)),
                ('language', models.CharField(max_length=8)),
                ('is_wechat', models.BooleanField(default=False)),
                ('country', models.CharField(max_length=8)),
                ('region', models.CharField(blank=True, max_length=16, null=True, choices=[('\u5317\u4eac\u5e02', '\u5317\u4eac\u5e02'), ('\u4e0a\u6d77\u5e02', '\u4e0a\u6d77\u5e02'), ('\u9999\u6e2f', '\u9999\u6e2f'), ('\u53f0\u6e7e', '\u53f0\u6e7e'), ('\u91cd\u5e86\u5e02', '\u91cd\u5e86\u5e02'), ('\u6fb3\u95e8', '\u6fb3\u95e8'), ('\u5929\u6d25\u5e02', '\u5929\u6d25\u5e02'), ('\u6c5f\u82cf\u7701', '\u6c5f\u82cf\u7701'), ('\u6d59\u6c5f\u7701', '\u6d59\u6c5f\u7701'), ('\u56db\u5ddd\u7701', '\u56db\u5ddd\u7701'), ('\u6c5f\u897f\u7701', '\u6c5f\u897f\u7701'), ('\u798f\u5efa\u7701', '\u798f\u5efa\u7701'), ('\u9752\u6d77\u7701', '\u9752\u6d77\u7701'), ('\u5409\u6797\u7701', '\u5409\u6797\u7701'), ('\u8d35\u5dde\u7701', '\u8d35\u5dde\u7701'), ('\u9655\u897f\u7701', '\u9655\u897f\u7701'), ('\u5c71\u897f\u7701', '\u5c71\u897f\u7701'), ('\u6cb3\u5317\u7701', '\u6cb3\u5317\u7701'), ('\u6e56\u5317\u7701', '\u6e56\u5317\u7701'), ('\u8fbd\u5b81\u7701', '\u8fbd\u5b81\u7701'), ('\u6e56\u5357\u7701', '\u6e56\u5357\u7701'), ('\u5c71\u4e1c\u7701', '\u5c71\u4e1c\u7701'), ('\u4e91\u5357\u7701', '\u4e91\u5357\u7701'), ('\u6cb3\u5357\u7701', '\u6cb3\u5357\u7701'), ('\u5e7f\u4e1c\u7701', '\u5e7f\u4e1c\u7701'), ('\u5b89\u5fbd\u7701', '\u5b89\u5fbd\u7701'), ('\u7518\u8083\u7701', '\u7518\u8083\u7701'), ('\u6d77\u5357\u7701', '\u6d77\u5357\u7701'), ('\u9ed1\u9f99\u6c5f\u7701', '\u9ed1\u9f99\u6c5f\u7701'), ('\u5185\u8499\u53e4\u81ea\u6cbb\u533a', '\u5185\u8499\u53e4\u81ea\u6cbb\u533a'), ('\u65b0\u7586\u7ef4\u543e\u5c14\u81ea\u6cbb\u533a', '\u65b0\u7586\u7ef4\u543e\u5c14\u81ea\u6cbb\u533a'), ('\u5e7f\u897f\u58ee\u65cf\u81ea\u6cbb\u533a', '\u5e7f\u897f\u58ee\u65cf\u81ea\u6cbb\u533a'), ('\u5b81\u590f\u56de\u65cf\u81ea\u6cbb\u533a', '\u5b81\u590f\u56de\u65cf\u81ea\u6cbb\u533a'), ('\u897f\u85cf\u81ea\u6cbb\u533a', '\u897f\u85cf\u81ea\u6cbb\u533a'), ('\u5176\u4ed6\u5730\u533a', '\u5176\u4ed6\u5730\u533a')])),
                ('reminded_jfs', models.BooleanField(default=False)),
                ('reminded_idg', models.BooleanField(default=False)),
                ('create_datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SignupCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_jfs', models.BooleanField(default=False)),
                ('is_idg', models.BooleanField(default=False)),
                ('value', models.CharField(unique=True, max_length=64)),
                ('used', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together=set([('signup_code_idg', 'signup_code_jfs')]),
        ),
    ]
