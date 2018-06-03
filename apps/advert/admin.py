from django.contrib import admin
from advert.models import AdAccount, AdCampaign


class AdAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'access_token', 'admin_user_id', 'fbid')
    list_display_links = list_display
admin.site.register(AdAccount, AdAccountAdmin)


class AdCampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'ad_account', 'fbid', 'is_active')
    list_display_links = list_display
admin.site.register(AdCampaign, AdCampaignAdmin)
