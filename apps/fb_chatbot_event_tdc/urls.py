from django.conf.urls import url
from django.contrib.auth import views as auth_views

from fb_chatbot_event_tdc import views


urlpatterns = [
    url(r'^766968e312f3c9949bd259b714d69146ff2664084b093f563e/?$',
        views.MessengerView.as_view()),
    url(r'^broadcast/(?P<fb_page_id>\d+)$', views.BroadcastView.as_view(),
        name='fb_chatbot_event_tdc_broadcast'),
    url(r'^broadcast/status/(?P<fb_page_id>\d+)$',
        views.BroadcastStatusView.as_view(),
        name='fb_chatbot_event_tdc_broadcast_status'),

    url(r'^fb-authentication$', views.FBAuthenticationView.as_view(),
        name='fb_chatbot_event_tdc_fb_auth'),
    url(r'^fb-auth-code$', views.FBAuthenticationCodeView.as_view(),
        name='fb_chatbot_event_tdc_fb_auth_code'),
    url(r'^fb-auth-pages$', views.FBAuthPages.as_view(),
        name='fb_chatbot_event_tdc_fb_auth_page'),
    url(r'^fb-auth-success$', views.FBAuthSuccessView.as_view(),
        name='fb_chatbot_event_tdc_fb_auth_success'),

    url(r'^send-reminder/(?P<fb_page_id>\d+)$',
        views.SendReminderView.as_view(),
        name='fb_chatbot_event_tdc_send_reminder'),
    url(r'^send-reminder/preview/$', views.SendReminderPreviewView.as_view(),
        name='fb_chatbot_event_tdc_send_reminder_preview'),
    url(r'^send-reminder/status/(?P<fb_page_id>\d+)$',
        views.SendReminderStatusView.as_view(),
        name='fb_chatbot_event_tdc_send_reminder_status'),

    url(r'^login/$', auth_views.login,
        {'template_name': 'fb_chatbot_event_tdc/login.html'},
        name='fb_chatbot_event_tdc_auth_login'),
    url(r'^logout/$', auth_views.logout_then_login,
        name='fb_chatbot_event_tdc_auth_logout')
]
