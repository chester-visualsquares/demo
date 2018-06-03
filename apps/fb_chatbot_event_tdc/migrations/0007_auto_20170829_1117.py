# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('fb_chatbot_event_tdc', '0006_facebookuser_auto_replied'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegisterReminderList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('reminded', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='fb_chatbot_event_tdc.Event')),
                ('fb_user', models.ForeignKey(to='fb_chatbot_event_tdc.FacebookUser')),
            ],
        ),
        migrations.AlterField(
            model_name='deliveredmessage',
            name='create_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='deliverypostback',
            name='create_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='signup',
            name='create_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='registerreminderlist',
            name='signup',
            field=models.ForeignKey(blank=True, to='fb_chatbot_event_tdc.Signup', null=True),
        ),
    ]
