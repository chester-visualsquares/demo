import logging
import os
import requests


from django.core.management.base import BaseCommand

from fb_chatbot_event_tdc.models import FacebookPage


logger = logging.getLogger('django.command')


class Command(BaseCommand):
    args = '<FacebookPage_pk>'
    help = ('Update the persistent menu of the Messenger. Reference:'
            'https://developers.facebook.com/docs/messenger-platform/'
            'thread-settings/persistent-menu')

    def handle(self, fb_pk, **options):
        with open(os.path.dirname(os.path.abspath(__file__)) +
                  '/persistent_menu.json', 'r+') as persistent_menu_file:
            access_token = FacebookPage.objects.get(pk=fb_pk).access_token
            params = {
                'persistent_menu': persistent_menu_file.read(),
            }
            url = ('https://graph.facebook.com/v2.8/me/'
                   'messenger_profile?access_token=%s' % access_token)
            response = requests.post(url, data=params)
            self.stdout.write(response.content)
