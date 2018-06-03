import ast
import json

from datetime import datetime

from django.apps import apps
from django.db import models
from django.utils import timezone


class FacebookPage(models.Model):
    fbid = models.BigIntegerField(unique=True)
    access_token = models.CharField(max_length=256)

    def __unicode__(self):
        return unicode(self.fbid)


class FacebookUser(models.Model):
    fb_page = models.ForeignKey('FacebookPage')
    fbid = models.BigIntegerField()
    unsubscribe = models.BooleanField(default=False)
    auto_replied = models.BooleanField(default=False)
    language = models.CharField(max_length=8, default='eng')

    class Meta:
        unique_together = ('fb_page', 'fbid')

    def __unicode__(self):
        return unicode(self.fbid)


class Event(models.Model):
    fb_page = models.ForeignKey('FacebookPage')
    project = models.ForeignKey('dashboard.Project',
                                related_name="%(app_label)s_%(class)s_related")
    name = models.CharField(max_length=128)
    name_chi = models.CharField(max_length=32, blank=True)
    app_model_path = models.CharField(max_length=128)
    # Determine which event the contact object registered.
    contact_filters = models.CharField(max_length=64, blank=True, default='{}')
    signup_code_attr = models.CharField(max_length=32, default='signup_code')
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=128)
    venue_chi = models.CharField(max_length=128, blank=True)
    signup_info_page_url_str = models.URLField()
    signup_page_url_str = models.URLField()
    event_page_url_str = models.URLField()
    gift_message = models.TextField(max_length=640, blank=True, null=True)
    gift_message_chi = models.TextField(max_length=640, blank=True, null=True)
    event_image_url_str = models.URLField()

    @property
    def app_model(self):
        return apps.get_model(*self.app_model_path.split('.'))

    @property
    def contact_filters_dict(self):
        return json.loads(self.contact_filters)

    def __unicode__(self):
        return self.name


class ReceivedMessage(models.Model):
    fb_page = models.ForeignKey('FacebookPage')
    fb_user = models.ForeignKey('FacebookUser')
    timestamp = models.CharField(max_length=16)
    mid = models.CharField(max_length=128, unique=True)
    seq = models.BigIntegerField()
    message = models.TextField(blank=True, null=True)
    responded = models.BooleanField(default=False)

    @property
    def timestamp_dt(self):
        return datetime.fromtimestamp(float(self.timestamp) / 1000.0)


class ReceivedPostback(models.Model):
    fb_page = models.ForeignKey('FacebookPage')
    fb_user = models.ForeignKey('FacebookUser')
    timestamp = models.CharField(max_length=16)
    postback = models.TextField(blank=True, null=True)
    responded = models.BooleanField(default=False)

    @property
    def payload(self):
        return ast.literal_eval(self.postback)['payload']

    @property
    def timestamp_dt(self):
        return datetime.fromtimestamp(float(self.timestamp) / 1000.0)


class DeliveredMessage(models.Model):
    BROADCAST = 'BC'
    MESSAGE_TYPES = (
        (BROADCAST, 'Broadcast'),
    )
    fb_page = models.ForeignKey('FacebookPage')
    fb_user = models.ForeignKey('FacebookUser')
    category = models.CharField(max_length=2,
                                choices=MESSAGE_TYPES,
                                default=BROADCAST)
    create_datetime = models.DateTimeField(default=timezone.now)
    message = models.TextField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    response = models.TextField(blank=True, null=True)
    mid = models.CharField(max_length=128, blank=True, null=True)


class DeliveryPostback(models.Model):
    fb_page = models.ForeignKey('FacebookPage')
    fb_user = models.ForeignKey('FacebookUser')
    mid = models.CharField(max_length=128)
    watermark = models.BigIntegerField()
    seq = models.BigIntegerField()
    create_datetime = models.DateTimeField(default=timezone.now)


class Signup(models.Model):
    fb_user = models.ForeignKey('FacebookUser')
    contact = models.CharField(max_length=128)  # format: 'app.Model|pk'
    event = models.ForeignKey('Event')
    signup_code = models.CharField(max_length=64, unique=True)
    reminded_datetime = models.DateTimeField(blank=True, null=True)
    create_datetime = models.DateTimeField(default=timezone.now)

    @property
    def contact_object(self):
        pk = self.contact.split('|')[1]
        contact_model = apps.get_model(
            *self.contact.split('|')[0].split('.'))
        return contact_model.objects.get(pk=pk)

    def __unicode__(self):
        return '-'.join((str(self.fb_user.fbid),
                         self.contact, self.event.name))


class RegisterReminderList(models.Model):
    fb_user = models.ForeignKey('FacebookUser')
    event = models.ForeignKey('Event')
    create_datetime = models.DateTimeField(default=timezone.now)
    reminded = models.BooleanField(default=False)
    registered = models.BooleanField(default=False)
