# -*- coding: utf-8 -*-
import csv
import logging
import os

from django.core.management.base import LabelCommand
from django.utils import timezone
from django.utils.encoding import smart_str


from fb_chatbot_event_tdc.messaging import post_text_message
from fb_chatbot_event_tdc.models import Signup

logger = logging.getLogger('django.command')


class Command(LabelCommand):
    args = '<Signup pk>'
    help = ('Send broadcast messages in broadcast_message.txt '
            'to Facebook users.')

    def handle_label(self, label, **options):
        signup = Signup.objects.filter(pk=label,
                                        fb_user__unsubscribe=False).first()
        if not signup:
            return

        with open(os.path.dirname(os.path.abspath(__file__)) +
                  '/broadcast_message.txt', 'r+') as broadcast_message_file:
            message_text = broadcast_message_file.read()

        directory = os.path.dirname(os.path.abspath(__file__)
                                    ) + '/broadcast_log'
        if not os.path.exists(directory):
            os.makedirs(directory)

        broadcast_log_path = (directory + '/broadcast_log_%s.csv'
                              % str(timezone.now().date()))
        with open(broadcast_log_path, 'a') as broadcast_log_csv:
            fieldnames = ['Time', 'Facebook Page', 'Facebook User ID',
                          'Message Text', 'Status']
            writer = csv.DictWriter(broadcast_log_csv,
                                    fieldnames=fieldnames,
                                    delimiter='\t')

            if os.stat(broadcast_log_path).st_size == 0:
                writer.writeheader()

            status = post_text_message(signup.fb_user.fb_page,
                                       signup.fb_user.fbid, message_text)
            if status == 'Success':
                logger.info(
                    'Broadcast message have been sent to %s (Signup #%s).'
                    % (str(signup.fb_user.fbid), signup.pk))
            else:
                logger.error(
                    'Broadcast message failed to be sent to %s '
                    '(Signup #%s).'
                    % (str(signup.fb_user.fbid), signup.pk))

            writer.writerow({
                'Time': smart_str(timezone.now()),
                'Facebook Page': smart_str(signup.fb_user.fb_page.fbid),
                'Facebook User ID': smart_str(signup.fb_user.fbid),
                'Message Text': smart_str(message_text),
                'Status': smart_str(status),
            })
