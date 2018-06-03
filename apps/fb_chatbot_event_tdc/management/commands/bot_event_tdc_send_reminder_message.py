# -*- coding: utf-8 -*-
import csv
import logging
import os

from django.core.management.base import LabelCommand
from django.utils import timezone
from django.utils.encoding import smart_str


from fb_chatbot_event_tdc import utils
from fb_chatbot_event_tdc.messaging import post_button_message
from fb_chatbot_event_tdc.models import Signup

logger = logging.getLogger('django.command')


class Command(LabelCommand):
    args = '<Signup pk>'
    help = 'Send reminder messages to Facebook users.'

    def handle_label(self, label, **options):
        signup = Signup.objects.filter(pk=label,
                                       reminded_datetime__isnull=True,
                                       fb_user__unsubscribe=False).first()
        if not signup:
            return

        directory = os.path.dirname(os.path.abspath(__file__)
                                    ) + '/send_reminder_log'
        if not os.path.exists(directory):
            os.makedirs(directory)

        send_reminder_log_path = (directory + '/send_reminder_log_%s.csv'
                                  % str(timezone.now().date()))
        with open(send_reminder_log_path, 'a') as send_reminder_log_csv:
            fieldnames = ['Time', 'Facebook Page', 'Facebook User ID',
                          'Message Text', 'Button', 'Status']
            writer = csv.DictWriter(send_reminder_log_csv,
                                    fieldnames=fieldnames,
                                    delimiter='\t')

            if os.stat(send_reminder_log_path).st_size == 0:
                writer.writeheader()

            text, button = utils.reminder_message_button(signup.fb_user)
            status = post_button_message(signup.fb_user.fb_page,
                                         signup.fb_user.fbid, text, button)
            if status == 'Success':
                signup.reminded_datetime = timezone.now()
                signup.save()
                logger.info(
                    'Reminder message have been sent to %s (Signup %s).'
                    % (str(signup.fb_user.fbid), signup.pk))
            else:
                logger.error(
                    'Reminder message failed to be sent to %s '
                    '(Signup %s).'
                    % (str(signup.fb_user.fbid), signup.pk))

            writer.writerow({
                'Time': smart_str(timezone.now()),
                'Facebook Page': smart_str(signup.fb_user.fb_page.fbid),
                'Facebook User ID': smart_str(signup.fb_user.fbid),
                'Message Text': smart_str(text),
                'Button': smart_str(button),
                'Status': smart_str(status),
            })
