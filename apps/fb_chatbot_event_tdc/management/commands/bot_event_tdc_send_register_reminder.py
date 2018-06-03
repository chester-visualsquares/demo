# -*- coding: utf-8 -*-
import logging

from django.core.management.base import LabelCommand
from django.utils import timezone

from datetime import timedelta

from fb_chatbot_event_tdc import utils
from fb_chatbot_event_tdc.messaging import post_button_message
from fb_chatbot_event_tdc.models import (FacebookPage,
                                         RegisterReminderList)

logger = logging.getLogger('django.command')


class Command(LabelCommand):
    args = '<fb_page_id>'
    help = 'Send reminder messages to Facebook users.'

    def handle(self, fb_page_id, **options):
        event_list = FacebookPage.objects.get(fbid=fb_page_id).event_set.all()
        for event in event_list:
            reminder_list = RegisterReminderList.objects.filter(
                event=event, reminded=False, registered=False,
                create_datetime__range=(
                    timezone.now() - timedelta(hours=23, minutes=30),
                    timezone.now() - timedelta(hours=6)))

            for item in reminder_list:
                text, button = utils.reigster_reminder_message_button(
                    event, item.fb_user.language)
                status = post_button_message(item.fb_user.fb_page,
                                             item.fb_user.fbid,
                                             text, button)
                if status == 'Success':
                    item.reminded = True
                    item.save()
                    logger.info(
                        'Register reminder have been sent to %s at %s.'
                        % (str(item.fb_user.fbid), str(timezone.now())))
                else:
                    logger.error(
                        'Register reminder failed to be sent to %s at %s.'
                        % (str(item.fb_user.fbid), str(timezone.now())))
