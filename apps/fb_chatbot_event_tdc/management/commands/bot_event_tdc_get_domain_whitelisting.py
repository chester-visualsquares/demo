import logging
import json
import requests


from django.core.management.base import BaseCommand

from fb_chatbot_event_tdc.models import FacebookPage


logger = logging.getLogger('django.command')


class Command(BaseCommand):
    args = '<FacebookPage_pk>'
    help = ('Read the domain whitelist of the FB page. Reference:'
            'https://developers.facebook.com/docs/messenger-platform/'
            'thread-settings/domain-whitelisting')

    def handle(self, fb_pk, **options):
        access_token = FacebookPage.objects.get(pk=fb_pk).access_token
        whitelist_params = {
            'fields': 'whitelisted_domains',
            'access_token': access_token}
        whitelist_url = 'https://graph.facebook.com/v2.7/me/thread_settings'
        response = requests.get(whitelist_url,
                                whitelist_params).json()
        self.stdout.write(json.dumps(response))
