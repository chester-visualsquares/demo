from django import forms
from django.shortcuts import get_object_or_404

from fb_chatbot_event_tdc.models import Event, FacebookPage


class BroadcastForm(forms.Form):

    event = forms.ModelChoiceField(queryset=None,
                                   empty_label=None)
    message = forms.CharField(widget=forms.Textarea(),
                              label='Message',
                              required=True,
                              max_length=320)

    def __init__(self, *args, **kwargs):
        fb_page_id = kwargs.pop('fb_page_id', None)
        fb_page = get_object_or_404(FacebookPage, pk=fb_page_id)

        super(BroadcastForm, self).__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(fb_page=fb_page)


class SendReminderForm(forms.Form):
    event = forms.ModelChoiceField(queryset=None,
                                   empty_label='Choose the event...')

    def __init__(self, *args, **kwargs):
        fb_page_id = kwargs.pop('fb_page_id', None)
        fb_page = get_object_or_404(FacebookPage, pk=fb_page_id)

        super(SendReminderForm, self).__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(fb_page=fb_page)
