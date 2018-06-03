from django.conf.urls import url
from django.contrib.auth import views as auth_views

from dashboard import views

urlpatterns = [
    url(r'^projects/$', views.projects, name='dashboard_projects'),
    url(r'^create-shorten-links/$', views.create_shorten_links,
        name='dashboard_create_shorten_links'),

    url(r'^project/(?P<project_id>\d+)/country-breakdown$',
        views.country_breakdown, name='dashboard_country_breakdown'),
    url(r'^project/(?P<project_id>\d+)/daily-report$',
        views.daily_report, name='dashboard_daily_report'),
    url(r'^project/(?P<project_id>\d+)/signup-list/(?P<network>\w+)$',
        views.signup_list, name='dashboard_signup_list'),
    url(r'^project/(?P<project_id>\d+)/channel-list$',
        views.channel_list, name='dashboard_channel_list'),

    url(r'^project/(?P<project_id>\d+)/download/signup-list/(?P<network>\w+)$',
        views.download_report, {'report_type': 'signup-list'},
        name='dashboard_download_signup_list'),
    url(r'^project/(?P<project_id>\d+)/download/(?P<report_type>[-\w]+)$',
        views.download_report, name='dashboard_download_report'),

    url(r'^login/$', auth_views.login,
        {'template_name': 'dashboard/login.html'}, name='dashboard_login'),
    url(r'^logout/$', auth_views.logout_then_login,
        name='dashboard_logout')
]
