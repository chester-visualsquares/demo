# -*- coding: utf-8 -*-
import binascii
import logging
import os
import urllib

from datetime import datetime
from time import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import LabelCommand
from django.template.loader import render_to_string
from html2text import html2text

from signup_mobile_tdc_hkjf17.models import Contact

logger = logging.getLogger('django.command')


class Command(LabelCommand):
    help = 'Send reminder emails to HKJF17 visitor with given ID. Mark ' \
           'the visitor as reminded afterwards.'

    def handle_label(self, label, **options):
        contacts = Contact.objects.filter(pk=label,
                                          reminded_1_jfs=False,
                                          attend_jfs=True)

        for contact in contacts:
            try:
                self.send_reminder(contact)
            except Exception as e:
                logger.error('Faild to send reminder email to %s: %s'
                             % (contact.pk, str(e)))
            else:
                logger.info('Send email to user %s' % contact.pk)
                contact.reminded_1_jfs = True
                contact.save()

    def send_reminder(self, contact):
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

        if contact.language == 'eng':
            subject = subject_eng
        elif contact.language == 'sc':
            subject = subject_sc
        elif contact.language == 'chi':
            subject = subject_chi

        from_email = settings.SNM_TDC_HKJF17_FROM_EMAIL
        to_email = contact.email
        html_template = ('signup_mobile_tdc_hkjf17/reminder_email_jfs_1.html')

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
            'gid': 'G-RMD-EMAIL',
            'cid': contact.auth_str,
            'laid': settings.SNM_TDC_HKJF17_FBCSID_PREFIX + '9800',
            'idgoal': 'G-RMD-EMAIL',
            'rec': 1,
            'url': 'https://a.wya.me/%s' % html_template,
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

        context = {
            'contact': contact,
            'settings': settings,
            'STATIC_URL': settings.STATIC_URL,
            'track_goal_url': '%s?%s' % (track_gif, query_string_goal),
        }

        html_content = render_to_string(html_template, context)
        text_content = html2text(html_content)

        email = EmailMultiAlternatives(subject, text_content, from_email,
                                       [to_email])
        email.attach_alternative(html_content, 'text/html')
        email.send()
