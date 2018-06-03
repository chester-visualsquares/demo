import logging
import json
import requests


from django.core.management.base import BaseCommand

from fb_chatbot_event_tdc.models import FacebookPage


logger = logging.getLogger('django.command')


class Command(BaseCommand):
    args = '<FacebookPage_pk><add/remove><domain str>'
    help = ('Change the domain whitelisting of the FB page. Reference:'
            'https://developers.facebook.com/docs/messenger-platform/'
            'thread-settings/domain-whitelisting')

    def handle(self, fb_pk, choice, domain_str, **options):
        if choice not in ('add', 'remove'):
            self.stderr.write('Either use "add" or "remove" for the args.')
            return
        access_token = FacebookPage.objects.get(pk=fb_pk).access_token

        whitelist_params = {
            'setting_type': 'domain_whitelisting',
            'whitelisted_domains': json.dumps([domain_str]),
            'domain_action_type': choice
        }
        whitelist_url = ('https://graph.facebook.com/v2.8/me/thread_settings'
                         '?access_token=%s' % access_token)
        response = requests.post(whitelist_url, data=whitelist_params)
        self.stdout.write(response.content)
