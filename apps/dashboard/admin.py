from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from dashboard.models import (Client,
                              DailyAdStats,
                              Project,
                              UserProfile,
                              Channel)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'timezone', 'daily_report_required',
                    'country_breakdown_required', 'signup_list_required')
    list_display_links = list_display
admin.site.register(Client, ClientAdmin)


class DailyAdStatsAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'impressions', 'clicks', 'link_clicks',
                    'spent', 'dollar_spent', 'conversions', 'ctr',
                    'website_ctr', 'cpc', 'cplc',
                    'conversion_rate', 'dollar_cpa', 'cpa_class')
    list_display_links = list_display
admin.site.register(DailyAdStats, DailyAdStatsAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'network',
                    'model_path', 'queryset_filters',
                    'country_field_name', 'cs_id', 'gid_pattern',
                    'aid_pattern', 'unique_by', 'attribution_window',
                    'cs_daily_sync_required',
                    'is_active', 'last_update')
    list_display_links = list_display
admin.site.register(Project, ProjectAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'client', 'timezone')
    list_display_links = list_display
admin.site.register(UserProfile, UserProfileAdmin)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class ChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'aid',
                    'network', 'short_url')
    list_display_links = list_display
admin.site.register(Channel, ChannelAdmin)
