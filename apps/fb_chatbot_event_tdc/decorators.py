from django.http import Http404
from django.shortcuts import get_object_or_404

from dashboard.models import Client
from fb_chatbot_event_tdc.models import FacebookPage


def client_hktdc_required(func):
    def wrapped(request, *args, **kwargs):
        profile = request.user.profile

        if profile.client != Client.objects.get(pk=1):
            raise Http404
        request.client = profile.client
        return func(request, *args, **kwargs)
    return wrapped


def fb_page_required(func):
    def wrapped(request, *args, **kwargs):
        fb_page = get_object_or_404(FacebookPage,
                                    pk=kwargs['fb_page_id'])
        request.fb_page = fb_page
        return func(request, *args, **kwargs)
    return wrapped
