from django.conf.urls import url

from adsops import views

urlpatterns = [
    url(r'^performance-tracker/$', views.performance_tracker,
        name='adsops_performance_tracker'),
]
