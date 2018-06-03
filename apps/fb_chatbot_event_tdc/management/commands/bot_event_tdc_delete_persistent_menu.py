import logging
import requests


from django.core.management.base import BaseCommand

from fb_chatbot_event_tdc.models import FacebookPage


logger = logging.getLogger('django.command')


class Command(BaseCommand):
    args = '<FacebookPage_pk>'
    help = ('Delete the persistent menu of the Messenger. Reference:'
            'https://developers.facebook.com/docs/messenger-platform/'
            'thread-settings/persistent-menu')

    def handle(self, fb_pk, **options):
        access_token = FacebookPage.objects.get(pk=fb_pk).access_token
        params = {
            'setting_type': 'call_to_actions',
            'thread_state': 'existing_thread',
        }
        url = ('https://graph.facebook.com/v2.8/me/'
               'thread_settings?access_token=%s' % access_token)
        response = requests.delete(url, data=params)
        self.stdout.write(response.content)
