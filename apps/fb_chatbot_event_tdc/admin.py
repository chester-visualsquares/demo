from django.contrib import admin

from fb_chatbot_event_tdc.models import (DeliveredMessage,
                                         DeliveryPostback,
                                         Event,
                                         FacebookPage,
                                         FacebookUser,
                                         ReceivedMessage,
                                         ReceivedPostback,
                                         RegisterReminderList,
                                         Signup)


class DeliveredMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_user', 'category', 'message', 'mid',
                    'acknowledged', 'response', 'create_datetime')
    list_display_links = list_display
admin.site.register(DeliveredMessage, DeliveredMessageAdmin)


class DeliveryPostbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_user', 'mid',
                    'watermark', 'seq', 'create_datetime')
    list_display_links = list_display
admin.site.register(DeliveryPostback, DeliveryPostbackAdmin)


class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name',
                    'app_model_path', 'contact_filters',
                    'start_date', 'end_date', 'venue',
                    'signup_page_url_str', 'event_page_url_str',
                    'gift_message')
    list_display_links = list_display
admin.site.register(Event, EventAdmin)


class FacebookPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'fbid', 'access_token')
    list_display_links = list_display
admin.site.register(FacebookPage, FacebookPageAdmin)


class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_page', 'fbid', 'unsubscribe', 'auto_replied',
                    'language')
    list_display_links = list_display
admin.site.register(FacebookUser, FacebookUserAdmin)


class ReceivedMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_user', 'timestamp_dt', 'mid', 'seq',
                    'message', 'responded')
    list_display_links = list_display
admin.site.register(ReceivedMessage, ReceivedMessageAdmin)


class ReceivedPostbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_user', 'payload',
                    'responded', 'timestamp_dt')
    list_display_links = list_display
admin.site.register(ReceivedPostback, ReceivedPostbackAdmin)


class SignupAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_user', 'contact', 'event', 'signup_code',
                    'reminded_datetime', 'create_datetime')
    list_display_links = list_display
admin.site.register(Signup, SignupAdmin)


class RegisterReminderListAdmin(admin.ModelAdmin):
    list_display = ('id', 'fb_user', 'event', 'create_datetime',
                    'reminded', 'registered')
    list_display_links = list_display
admin.site.register(RegisterReminderList, RegisterReminderListAdmin)
