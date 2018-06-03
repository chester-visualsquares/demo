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
from signup_mobile_tdc_hkjf17.constants import (CHINESE,
                                                ENGLISH,
                                                REGION_CHOICES,
                                                SIMPLIFIED_CHINESE)


class ContactManager(models.Manager):

    def report_fields(self):
        return ['Ref.', 'First Name', 'Last Name', 'Company',
                'Company Email', 'Country Code', 'Mobile Phone',
                'Country', 'Region',
                'Diamond Bar Code', 'Jewellery Bar Code',
                'Attend Diamond', 'Attend Jewellery',
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
                 'Country': signup.country_iso3,
                 'Region': signup.region,
                 'Attend Diamond': signup.attend_idg,
                 'Attend Jewellery': signup.attend_jfs,
                 'Diamond Bar Code': signup.signup_code_idg,
                 'Jewellery Bar Code': signup.signup_code_jfs,
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
            [('Diamond Fair Signups (%s)' % network_repr,
              signups.filter(attend_idg=True).count()),
             ('Jewellery Fair Signups (%s)' % network_repr,
              signups.filter(attend_jfs=True).count()),
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


class Contact(models.Model):
    first_name = models.CharField(max_length=128, blank=False)
    last_name = models.CharField(max_length=128, blank=False)
    company = models.CharField(max_length=128, blank=False)
    email = models.EmailField(max_length=256, blank=False)
    country_code = models.IntegerField(blank=False)
    mobile_phone = PhoneNumberField(blank=False, validate_required=False)

    attend_jfs = models.BooleanField(default=True)
    attend_idg = models.BooleanField(default=True)

    signup_code_jfs = models.CharField(
        max_length=64, unique=True, null=True, blank=True, default=None)
    signup_code_idg = models.CharField(
        max_length=64, unique=True, null=True, blank=True, default=None)

    language = models.CharField(max_length=8)
    is_wechat = models.BooleanField(default=False)
    country = models.CharField(max_length=8)
    region = models.CharField(max_length=16, null=True, blank=True,
                              choices=REGION_CHOICES)
    reminded_1_jfs = models.BooleanField(default=False)
    reminded_1_idg = models.BooleanField(default=False)
    reminded_2_jfs = models.BooleanField(default=False)
    reminded_2_idg = models.BooleanField(default=False)

    is_show_mgr_btn = models.BooleanField(default=False)
    used_fb_mgr = models.BooleanField(default=False)
    auth_str = models.CharField(max_length=32, unique=True)
    aid = models.CharField(max_length=16, null=True)
    is_mobile = models.BooleanField(default=False)

    create_datetime = models.DateTimeField(auto_now_add=True)

    objects = ContactManager()

    class Meta:
        unique_together = ('signup_code_idg', 'signup_code_jfs')

    @property
    def country_iso3(self):
        return pycountry.countries.get(alpha2=self.country.upper()).alpha3


class SignupCode(models.Model):
    is_jfs = models.BooleanField(default=False)
    is_idg = models.BooleanField(default=False)
    value = models.CharField(max_length=64, unique=True)
    used = models.BooleanField(default=False)


def signupcode_usage(sender, instance=None, created=False, **kwargs):
    if created:
        return

    if instance.pk > settings.SNM_TDC_HKJF17_SIGNUP_CODE_NUM_IDG:
        # idg fair signup code issued
        total = settings.SNM_TDC_HKJF17_SIGNUP_CODE_NUM_JFS
        used = instance.pk - settings.SNM_TDC_HKJF17_SIGNUP_CODE_NUM_IDG
    else:
        total = settings.SNM_TDC_HKJF17_SIGNUP_CODE_NUM_IDG
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

    from_email = settings.SNM_TDC_HKJF17_FROM_EMAIL
    to_email = instance.email
    ts = int(time())
    dt = datetime.fromtimestamp(time())

    query_string_goal = urllib.urlencode({
        'idsite': settings.SNM_TDC_HKJF17_CS_EMAIL_ACCOUNT_ID,
        'r': binascii.hexlify(os.urandom(3)),
        '_id': binascii.hexlify(os.urandom(8)),
        '_idts': ts,
        '_idvc': 1,
        '_nowts': ts,
        '_viewts': ts,
        '_idn': 0,
        'gid': 'G-CONF-EMAIL',
        'cid': instance.auth_str,
        'laid': settings.SNM_TDC_HKJF17_FBCSID_PREFIX + '9800',
        'idgoal': 'G-CONF-EMAIL',
        'rec': 1,
        'url': ('https://a.wya.me/%s/signup-email'
                % settings.SNM_TDC_HKJF17_URL_ROOT),
        'urlref': ('https://a.wya.me/%s/'
                   % settings.SNM_TDC_HKJF17_URL_ROOT),
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

    if instance.attend_idg:
        subject_eng = (u'HKTDC {0} ({1:%b} {1.day} - {2:%b} {2.day} {1:%Y})'
                       ).format(
            settings.SNM_TDC_HKJF17_FAIR_NAME_ENG_IDG,
            settings.SNM_TDC_HKJF17_START_DATE_IDG,
            settings.SNM_TDC_HKJF17_END_DATE_IDG
        )
        subject_chi = (u'香港貿發局{0} ({1:%Y}年{1.month}月{1.day}日'
                       u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKJF17_FAIR_NAME_CHI_IDG,
            settings.SNM_TDC_HKJF17_START_DATE_IDG,
            settings.SNM_TDC_HKJF17_END_DATE_IDG
        )
        subject_sc = (u'香港贸发局{0} ({1:%Y}年{1.month}月{1.day}日'
                      u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKJF17_FAIR_NAME_SC_IDG,
            settings.SNM_TDC_HKJF17_START_DATE_IDG,
            settings.SNM_TDC_HKJF17_END_DATE_IDG
        )
        if instance.language == ENGLISH:
            subject = subject_eng
        elif instance.language == CHINESE:
            subject = subject_chi
        elif instance.language == SIMPLIFIED_CHINESE:
            subject = subject_sc

        html_content = render_to_string(
            'signup_mobile_tdc_hkjf17/signup_email_idg.html',
            context_dict)

        text_content = html2text(html_content)
        email = EmailMultiAlternatives(subject, text_content, from_email,
                                       [to_email])
        email.attach_alternative(html_content, 'text/html')
        email.send()

    if instance.attend_jfs:
        subject_eng = (u'HKTDC {0} ({1:%b} {1.day} - {2:%b} {2.day} {1:%Y})'
                       ).format(
            settings.SNM_TDC_HKJF17_FAIR_NAME_ENG_JFS,
            settings.SNM_TDC_HKJF17_START_DATE_JFS,
            settings.SNM_TDC_HKJF17_END_DATE_JFS
        )
        subject_chi = (u'香港貿發局{0} ({1:%Y}年{1.month}月{1.day}日'
                       u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKJF17_FAIR_NAME_CHI_JFS,
            settings.SNM_TDC_HKJF17_START_DATE_JFS,
            settings.SNM_TDC_HKJF17_END_DATE_JFS
        )
        subject_sc = (u'香港贸发局{0} ({1:%Y}年{1.month}月{1.day}日'
                      u'至{2.month}月{2.day}日)').format(
            settings.SNM_TDC_HKJF17_FAIR_NAME_SC_JFS,
            settings.SNM_TDC_HKJF17_START_DATE_JFS,
            settings.SNM_TDC_HKJF17_END_DATE_JFS
        )

        if instance.language == ENGLISH:
            subject = subject_eng
        elif instance.language == CHINESE:
            subject = subject_chi
        elif instance.language == SIMPLIFIED_CHINESE:
            subject = subject_sc

        html_content = render_to_string(
            'signup_mobile_tdc_hkjf17/signup_email_jfs.html',
            context_dict)

        text_content = html2text(html_content)
        email = EmailMultiAlternatives(subject, text_content, from_email,
                                       [to_email])
        email.attach_alternative(html_content, 'text/html')
        email.send()
post_save.connect(signup_email, sender=Contact)
