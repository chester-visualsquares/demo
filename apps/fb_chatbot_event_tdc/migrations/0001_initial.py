# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_project_cs_daily_sync_required'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveredMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(default=b'BC', max_length=2, choices=[(b'BC', b'Broadcast')])),
                ('create_datetime', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField(null=True, blank=True)),
                ('acknowledged', models.BooleanField(default=False)),
                ('response', models.TextField(null=True, blank=True)),
                ('mid', models.CharField(unique=True, max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryPostback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mid', models.CharField(max_length=128)),
                ('watermark', models.BigIntegerField()),
                ('seq', models.BigIntegerField()),
                ('create_datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('app_model_path', models.CharField(max_length=128)),
                ('contact_filters', models.CharField(default=b'{}', max_length=64, blank=True)),
                ('signup_code_attr', models.CharField(default=b'signup_code', max_length=32)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('venue', models.CharField(max_length=128)),
                ('signup_page_url_str', models.URLField()),
                ('event_page_url_str', models.URLField()),
                ('gift_message', models.TextField(max_length=640, null=True, blank=True)),
                ('event_image_url_str', models.URLField()),
                ('reminder_messages', models.TextField(max_length=320, null=True, blank=True)),
                ('project', models.ForeignKey(related_name='fb_chatbot_event_tdc_event_related', to='dashboard.Project')),
            ],
        ),
        migrations.CreateModel(
            name='FacebookUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fbid', models.BigIntegerField(unique=True)),
                ('unsubscribe', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ReceivedMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.CharField(max_length=16)),
                ('mid', models.CharField(unique=True, max_length=128)),
                ('seq', models.BigIntegerField()),
                ('message', models.TextField(null=True, blank=True)),
                ('responded', models.BooleanField(default=False)),
                ('fb_user', models.ForeignKey(to='fb_chatbot_event_tdc.FacebookUser')),
            ],
        ),
        migrations.CreateModel(
            name='ReceivedPostback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.CharField(max_length=16)),
                ('postback', models.TextField(null=True, blank=True)),
                ('responded', models.BooleanField(default=False)),
                ('fb_user', models.ForeignKey(to='fb_chatbot_event_tdc.FacebookUser')),
            ],
        ),
        migrations.CreateModel(
            name='Signup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contact', models.CharField(max_length=128)),
                ('signup_code', models.CharField(unique=True, max_length=64)),
                ('reminded_datetime', models.DateTimeField(null=True, blank=True)),
                ('create_datetime', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(to='fb_chatbot_event_tdc.Event')),
                ('fb_user', models.ForeignKey(to='fb_chatbot_event_tdc.FacebookUser')),
            ],
        ),
        migrations.AddField(
            model_name='deliverypostback',
            name='fb_user',
            field=models.ForeignKey(to='fb_chatbot_event_tdc.FacebookUser'),
        ),
        migrations.AddField(
            model_name='deliveredmessage',
            name='fb_user',
            field=models.ForeignKey(to='fb_chatbot_event_tdc.FacebookUser'),
        ),
    ]
