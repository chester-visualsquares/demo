# -*- coding: utf-8 -*-
from datetime import timedelta

from django import forms, utils

from dashboard.models import Channel, Project


class ChannelForm(forms.ModelForm):
    PLATFORM_CHOICES = (
        ('FBC', 'Chinese - non-China Region'),
        ('FBE', 'English - non-China Region'),
        ('WEC', 'China Region'),
    )
    platform = forms.ChoiceField(choices=PLATFORM_CHOICES)

    class Meta:
        model = Channel
        fields = ['project', 'name']

    def __init__(self, *args, **kwargs):
        client = kwargs.pop('client')
        super(ChannelForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(
            client=client, is_active=True,
            last_update__gte=utils.timezone.now() - timedelta(days=60)
            ).order_by('-last_update')
        self.fields['project'].empty_label = None

    def clean(self):
        cleaned_data = super(ChannelForm, self).clean()
        cn_url = cleaned_data.get('project').cn_url
        chi_url = cleaned_data.get('project').non_cn_url_chi
        eng_url = cleaned_data.get('project').non_cn_url_eng

        if cn_url == "" and cleaned_data.get('platform') == 'WEC' or \
           chi_url == "" and cleaned_data.get('platform') == 'FBC' or \
           eng_url == "" and cleaned_data.get('platform') == 'FBE':
            raise forms.ValidationError("The selected project is not defined.")
