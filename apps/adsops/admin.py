from django.contrib import admin
from adsops.models import AdCampaignSettings


class AdCampaignSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'project', 'start_date', 'end_date',
                    'cpa_target_1', 'cpa_target_2', 'budget', 'is_active')
    list_display_links = list_display
admin.site.register(AdCampaignSettings, AdCampaignSettingsAdmin)
