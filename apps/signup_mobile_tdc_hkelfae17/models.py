# -*- coding: utf-8 -*-
import binascii
import os
import urllib

from collections import OrderedDict
from datetime import datetime, timedelta
from time import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.db import models
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from html2text import html2text
import pycountry
import pytz


from common.models import PhoneNumberField
from signup_mobile_tdc_hkelfae17.constants import (CHINESE,
                                                   ENGLISH,
                                                   REGION_CHOICES,
                                                   SIMPLIFIED_CHINESE)


class ContactManager(models.Manager):

    def report_fields(self):
        return ['Ref.', 'First Name', 'Last Name', 'Company',
                'Company Email', 'Country Code', 'Mobile Phone',
                'Country per mobile phone', 'Region', 'EU disclaimer',
                'Light Bar Code', 'Elec Bar Code',
                'Attend Light', 'Attend Elec',
                'Signup Time']

    def signup_report(self, network, filters):
        signups = super(ContactManager, self).get_queryset().order_by(
            '-create_datetime')

        if network == 'facebook':
            signups = signups.filter(is_wechat=False)

        elif network == 'wechat':
            signups = signups.filter(is_wechat=True)

        signups = signups.filter(**filters)

        return [{'Ref.': signup.id,
                 'First Name': signup.first_name,
                 'Last Name': signup.last_name,
                 'Company': signup.company,
                 'Company Email': signup.email,
                 'Country Code': signup.country_code,
                 'Mobile Phone': signup.mobile_phone,
                 'Country per mobile phone': signup.country_iso3,
                 'Region': signup.region,
                 'EU disclaimer': signup.eu_disclaimer,
                 'Attend Light': signup.attend_light,
                 'Attend Elec': signup.attend_elec,
                 'Light Bar Code': signup.signup_code_light,
                 'Elec Bar Code': signup.signup_code_elec,
                 'Signup Time': signup.create_datetime
                 } for signup in signups]

    def signup_breakdown(self, filters, network=None):
        signups = super(ContactManager, self).get_queryset()
        if network == 'facebook':
            signups = signups.filter(is_wechat=False)
            network_repr = 'Facebook'

        elif network == 'wechat':
            signups = signups.filter(is_wechat=True)
            network_repr = 'Wechat'

        elif not network:
            network_repr = 'All'

        signups = signups.filter(**filters)

        return OrderedDict(
            [('Light Fair Signups (%s)' % network_repr,
              signups.filter(attend_light=True).count()),
             ('Elec Fair Signups (%s)' % network_repr,
              signups.filter(attend_elec=True).count()),
             ])

    def daily_conversion(self, dt_local, filters, include_wechat=False):
        signups = super(ContactManager, self).get_queryset()
        if not include_wechat:
            signups = signups.filter(is_wechat=False)

        signups = signups.filter(**filters)

        dt_min = dt_local.astimezone(pytz.utc)
        dt_max = dt_min + timedelta(days=1)
        signups = signups.filter(create_datetime__gte=dt_min,
                                 create_datetime__lt=dt_max)
        return signups.count()

    def channel_report_fields(self):
        return ['Ref.', 'Channel', 'Platform', 'Shorten Link',
                'Elec Signups', 'Light Signups']

    def channel_report(self, channel_list):
        signups = super(ContactManager, self).get_queryset()

        return [{'Ref.': channel.id,
                 'Channel': channel.name,
                 'Platform': '%s (%s)' % (channel.get_network_display(),
                                          channel.get_language_display()),
                 'Shorten Link': channel.short_url,
                 'Elec Signups': signups.filter(aid=channel.aid,
                                                attend_elec=True).count(),
                 'Light Signups': signups.filter(aid=channel.aid,
                                                 attend_light=True).count(),
                 } for channel in channel_list]


class Contact(models.Model):
    first_name = models.CharField(max_length=128, blank=False)
    last_name = models.CharField(max_length=128, blank=False)
    company = models.CharField(max_length=128, blank=False)
    email = models.EmailField(max_length=256, blank=False)
    country_code = models.IntegerField(blank=False)
    mobile_phone = PhoneNumberField(blank=False, validate_required=False)

    attend_elec = models.BooleanField(default=False)
    attend_light = models.BooleanField(default=True)

    signup_code_elec = models.CharField(
        max_length=64, unique=True, null=True, blank=True, default=None)
    signup_code_light = models.CharField(
        max_length=64, unique=True, null=True, blank=True, default=None)

    language = models.CharField(max_length=8)
    is_wechat = models.BooleanField(default=False)
    country = models.CharField(max_length=8)
    region = models.CharField(max_length=16, null=True, blank=True,
                              choices=REGION_CHOICES)
    reminded_1_elec = models.BooleanField(default=False)
    reminded_1_light = models.BooleanField(default=False)
    reminded_2_elec = models.BooleanField(default=False)
    reminded_2_light = models.BooleanField(default=False)

    is_show_mgr_btn = models.BooleanField(default=False)
    used_fb_mgr = models.BooleanField(default=False)
    auth_str = models.CharField(max_length=32, unique=True)
    aid = models.CharField(max_length=16, null=True)
    is_mobile = models.BooleanField(default=False)
    eu_disclaimer = models.BooleanField(default=False)

    create_datetime = models.DateTimeField(auto_now_add=True)

    objects = ContactManager()

    class Meta:
        unique_together = ('signup_code_light', 'signup_code_elec')

    @property
    def country_iso3(self):
        return pycountry.countries.get(alpha2=self.country.upper()).alpha3


class SignupCode(models.Model):
    is_elec = models.BooleanField(default=False)
    is_light = models.BooleanField(default=False)
    value = models.CharField(max_length=64, unique=True)
    used = models.BooleanField(default=False)


def signupcode_usage(sender, instance=None, created=False, **kwargs):
    if created:
        return

    if instance.pk > settings.SNM_TDC_HKELFAE17_SIGNUP_CODE_NUM_LF:
        # idg fair signup code issued
        total = settings.SNM_TDC_HKELFAE17_SIGNUP_CODE_NUM_EF
        used = instance.pk - settings.SNM_TDC_HKELFAE17_SIGNUP_CODE_NUM_LF
    else:
        total = settings.SNM_TDC_HKELFAE17_SIGNUP_CODE_NUM_LF
        used = instance.pk

    unused = total - used
    if unused <= 200 and not unused % 20:
        subject = (u'Warning - %s SignupCode is running out' %
                   SignupCode._meta.app_label)
        message = u'SignupCode of %s has %d left' % (
            SignupCode._meta.app_label, unused)
        mail_admins(subject=subject, message=message)
post_save.connect(signupcode_usage, sender=SignupCode)


def signup_email(sender, instance=None, created=False, **kwargs):
    if not created:
        return

    from_email = settings.SNM_TDC_HKELFAE17_FROM_EMAIL
    to_email = instance.email
    ts = int(time())
    dt = datetime.fromtimestamp(time())

    query_string_goal = urllib.urlencode({
        'idsite': settings.SNM_TDC_HKELFAE17_CS_EMAIL_ACCOUNT_ID,
        'r': binascii.hexlify(os.urandom(3)),
        '_id': binascii.hexlify(os.urandom(8)),
        '_idts': ts,
        '_idvc': 1,
        '_nowts': ts,
        '_viewts': ts,
        '_idn': 0,
        'gid': 'G-CONF-EMAIL',
        'cid': instance.auth_str,
        'laid': settings.SNM_TDC_HKELFAE17_FBCSID_PREFIX + '9800',
        'idgoal': 'G-CONF-EMAIL',
        'rec': 1,
        'url': ('https://a.wya.me/%s/signup-email'
                % settings.SNM_TDC_HKELFAE17_URL_ROOT),
        'urlref': ('https://a.wya.me/%s/'
                   % settings.SNM_TDC_HKELFAE17_URL_ROOT),
        'h': dt.hour,
        'm': dt.minute,
        's': dt.second,
        '_refts': 0,
        'pdf': 1,
        'qt': 0,
        'realp': 0,
        'wma': 0,
        'dir': 0,
        'fla': 1,
        'java': 0,
        'gears': 0,
        'ag': 0,
        'res': '1440x900',
        'cookie': 1,
    })
    track_gif = 'http://d2dj4eyr0s9m9l.cloudfront.net/t.gif'

    context_dict = {
        'contact': instance,
        'settings': settings,
        'STATIC_URL': settings.STATIC_URL,
        'track_goal_url': '%s?%s' % (track_gif, query_string_goal),
    }

    if instance.attend_light:
        subject_eng = (u'HKTDC {0} ({1:%b} {1.day} - {2:%b} {2.day} {1:%Y})'
                       ).format(
            settings.SNM_TDC_HKELFAE17_FAIR_NAME_ENG_LF,
            settings.SNM_TDC_HKELFAE17_START_DATE_LF,
            settings.SNM_TDC_HKELFAE17_END_DATE_LF
        )
        subject_chi = (u'香港貿發局{0} ({1:%Y}年{1.month}月{1.day}日'
                       u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKELFAE17_FAIR_NAME_CHI_LF,
            settings.SNM_TDC_HKELFAE17_START_DATE_LF,
            settings.SNM_TDC_HKELFAE17_END_DATE_LF
        )
        subject_sc = (u'香港贸发局{0} ({1:%Y}年{1.month}月{1.day}日'
                      u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKELFAE17_FAIR_NAME_SC_LF,
            settings.SNM_TDC_HKELFAE17_START_DATE_LF,
            settings.SNM_TDC_HKELFAE17_END_DATE_LF
        )
        if instance.language == ENGLISH:
            subject = subject_eng
        elif instance.language == CHINESE:
            subject = subject_chi
        elif instance.language == SIMPLIFIED_CHINESE:
            subject = subject_sc

        html_content = render_to_string(
            'signup_mobile_tdc_hkelfae17/signup_email_light.html',
            context_dict)

        text_content = html2text(html_content)
        email = EmailMultiAlternatives(subject, text_content, from_email,
                                       [to_email])
        email.attach_alternative(html_content, 'text/html')
        email.send()

    if instance.attend_elec:
        subject_eng = (u'HKTDC {0} ({1:%b} {1.day} - {2:%b} {2.day} {1:%Y})'
                       ).format(
            settings.SNM_TDC_HKELFAE17_FAIR_NAME_ENG_EF,
            settings.SNM_TDC_HKELFAE17_START_DATE_EF,
            settings.SNM_TDC_HKELFAE17_END_DATE_EF
        )
        subject_chi = (u'香港貿發局{0} ({1:%Y}年{1.month}月{1.day}日'
                       u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKELFAE17_FAIR_NAME_CHI_EF,
            settings.SNM_TDC_HKELFAE17_START_DATE_EF,
            settings.SNM_TDC_HKELFAE17_END_DATE_EF
        )
        subject_sc = (u'香港贸发局{0} ({1:%Y}年{1.month}月{1.day}日'
                      u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKELFAE17_FAIR_NAME_SC_EF,
            settings.SNM_TDC_HKELFAE17_START_DATE_EF,
            settings.SNM_TDC_HKELFAE17_END_DATE_EF
        )

        if instance.language == ENGLISH:
            subject = subject_eng
        elif instance.language == CHINESE:
            subject = subject_chi
        elif instance.language == SIMPLIFIED_CHINESE:
            subject = subject_sc

        html_content = render_to_string(
            'signup_mobile_tdc_hkelfae17/signup_email_elec.html',
            context_dict)

        text_content = html2text(html_content)
        email = EmailMultiAlternatives(subject, text_content, from_email,
                                       [to_email])
        email.attach_alternative(html_content, 'text/html')
        email.send()
post_save.connect(signup_email, sender=Contact)
