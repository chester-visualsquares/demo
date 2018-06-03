from django.contrib import admin

from signup_mobile_tdc_hkjf17.models import Contact


class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'company', 'email',
                    'country_code', 'mobile_phone',
                    'attend_jfs', 'attend_idg',
                    'is_wechat', 'country', 'country_iso3', 'region',
                    'is_mobile', 'aid',
                    'language', 'is_show_mgr_btn', 'used_fb_mgr',
                    'signup_code_jfs', 'signup_code_idg',
                    'create_datetime')
    list_display_links = list_display
admin.site.register(Contact, ContactAdmin)
