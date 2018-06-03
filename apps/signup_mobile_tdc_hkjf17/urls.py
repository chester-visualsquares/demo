from django.conf.urls import url

from signup_mobile_tdc_hkjf17 import views

urlpatterns = [
    url(r'^$', views.landing, name='snm_tdc_hkjf17_landing'),
    # Trailing slash required by FB settings
    url(r'^canvas/$', views.canvas_landing,
        name='snm_tdc_hkjf17_canvas_landing'),

    url(r'^info$', views.info, name='snm_tdc_hkjf17_info'),
    url(r'^signup$', views.signup, name='snm_tdc_hkjf17_signup'),
    url(r'^thanks$', views.thanks, name='snm_tdc_hkjf17_thanks'),

    # URLs for mobile devices
    url(r'^m/info$', views.info,
        {'mobile': True}, name='snm_tdc_hkjf17_info_mobile'),
    url(r'^m/signup$', views.signup,
        {'mobile': True}, name='snm_tdc_hkjf17_signup_mobile'),
    url(r'^m/thanks$', views.thanks,
        {'mobile': True}, name='snm_tdc_hkjf17_thanks_mobile'),

    url(r'^info-website$', views.info_website,
        {'network': 'website'}, name='snm_tdc_hkjf17_info_website'),
    url(r'^signup-website$', views.signup_website,
        {'network': 'website'}, name='snm_tdc_hkjf17_signup_website'),
    url(r'^thanks-website$', views.thanks_website,
        {'network': 'website'}, name='snm_tdc_hkjf17_thanks_website'),

    url(r'^m/info-wechat$', views.info_website,
        {'network': 'wechat'}, name='snm_tdc_hkjf17_info_wechat'),
    url(r'^m/signup-wechat$', views.signup_website,
        {'network': 'wechat'}, name='snm_tdc_hkjf17_signup_wechat'),
    url(r'^m/thanks-wechat$', views.thanks_website,
        {'network': 'wechat'}, name='snm_tdc_hkjf17_thanks_wechat'),
]
