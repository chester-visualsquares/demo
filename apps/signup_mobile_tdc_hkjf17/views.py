import base64
import binascii
import json
import logging
import os
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.decorators import mobile_enabled, language_enabled
from common.utils import logging_extra
from facebook.decorators import signed_request_required
from fb_chatbot_event_tdc.models import Event
from fb_chatbot_event_tdc.messaging import create_mgr_signups
from fb_chatbot_event_tdc.utils import mark_registered
from signup_mobile_tdc_hkjf17.constants import ENGLISH, SIMPLIFIED_CHINESE
from signup_mobile_tdc_hkjf17.forms import SignupForm, WechatSignupForm
from signup_mobile_tdc_hkjf17.models import Contact, SignupCode
from tracking.utils import track_visitor


logger = logging.getLogger('django.request.logger')


# Exclude CSRF guard to receive POST request from FB iframe.
@csrf_exempt
@require_http_methods(['POST'])
@signed_request_required(settings.SNM_TDC_HKJF17_FB_APP_SECRET)
@language_enabled
def canvas_landing(
        request,
        template_name='signup_mobile_tdc_hkjf17/canvas_landing.html'):
    aid = request.GET.get(settings.CS_TRACKING_PARAMETER, None)
    if aid:
        app_data = {
            settings.CS_TRACKING_PARAMETER: aid,
        }
        query_parm = (('app_data', json.dumps(app_data)),) + \
            settings.SNM_TDC_HKJF17_FB_PAGE_PARAM
    else:
        query_parm = settings.SNM_TDC_HKJF17_FB_PAGE_PARAM

    query_string = urllib.urlencode(query_parm)
    fb_page_url = '%s?%s' % (settings.SNM_TDC_HKJF17_FB_PAGE_URL,
                             query_string)

    logger.debug(str(query_string), extra=logging_extra(request))
    return render(request, template_name, {
        'fb_page_url': fb_page_url,
    })


# Exclude CSRF guard to receive POST request from FB iframe.
@csrf_exempt
@require_http_methods(['POST'])
@signed_request_required(settings.SNM_TDC_HKJF17_FB_APP_SECRET)
@language_enabled
def landing(request):
    signed_request = request.signed_request
    try:
        app_data = json.loads(signed_request.get('app_data', '{}'))
    except:
        logger.warning('Cannot decode app_data from FB signed request.',
                       extra=logging_extra(request))
        app_data = {}

    user_data = signed_request.get('user', None)
    track_visitor(request, user_data, app_data)

    return _redirect('snm_tdc_hkjf17_info', app_data)


@require_http_methods(['GET'])
@language_enabled
def info(request, mobile=False,
         template_name_desktop='signup_mobile_tdc_hkjf17/info.html',
         template_name_mobile='signup_mobile_tdc_hkjf17/info_mobile.html'):
    template_name = template_name_mobile if mobile else template_name_desktop
    next_url = (reverse('snm_tdc_hkjf17_signup_mobile') if mobile
                else reverse('snm_tdc_hkjf17_signup'))
    aid = request.GET.get(settings.CS_TRACKING_PARAMETER, None)

    return render(request, template_name, {
        'CS_ACCOUNT_ID': settings.SNM_TDC_HKJF17_CS_ACCOUNT_ID,
        'CS_TRACKING_PATH': settings.SNM_TDC_HKJF17_URL_ROOT,
        'aid': aid,
        'trackA': True,
        'next_url': next_url,
    })


@require_http_methods(['GET'])
@mobile_enabled
@language_enabled
def info_website(
        request, network, mobile=False,
        template_name_website='signup_mobile_tdc_hkjf17/info.html',
        template_name_wechat='signup_mobile_tdc_hkjf17/info_wechat.html',
        template_name_mobile='signup_mobile_tdc_hkjf17/info_mobile.html'):
    if network == 'website':
        template_name = (template_name_mobile
                         if mobile else template_name_website)
        next_url = reverse('snm_tdc_hkjf17_signup_website')
    elif network == 'wechat':
        template_name = template_name_wechat
        next_url = reverse('snm_tdc_hkjf17_signup_wechat')
        request.language = SIMPLIFIED_CHINESE

    aid = request.GET.get(settings.CS_TRACKING_PARAMETER, None)

    return render(request, template_name, {
        'CS_ACCOUNT_ID': settings.SNM_TDC_HKJF17_CS_ACCOUNT_ID,
        'CS_TRACKING_PATH': settings.SNM_TDC_HKJF17_URL_ROOT,
        'aid': aid,
        'is_cn': True if network == 'wechat' else False,
        'trackA': True,
        'network': network,
        'next_url': next_url,
    })


@require_http_methods(['GET', 'POST'])
@language_enabled
def signup(
        request, form_cls=SignupForm, mobile=False,
        template_name_desktop='signup_mobile_tdc_hkjf17/signup.html',
        template_name_mobile='signup_mobile_tdc_hkjf17/signup_mobile.html'):
    template_name = template_name_mobile if mobile else template_name_desktop
    next_view = ('snm_tdc_hkjf17_thanks_mobile'
                 if mobile else 'snm_tdc_hkjf17_thanks')

    aid = request.GET.get(settings.CS_TRACKING_PARAMETER, None)

    if request.method == 'GET':
        form = form_cls(language=request.language)
        return render(request, template_name, {
            'CS_ACCOUNT_ID': settings.SNM_TDC_HKJF17_CS_ACCOUNT_ID,
            'CS_TRACKING_PATH': settings.SNM_TDC_HKJF17_URL_ROOT,
            'aid': aid,
            'form': form,
            'trackA': True,
        })

    elif request.method == 'POST':
        logger.debug(str(request.POST), extra=logging_extra(request))
        form = form_cls(data=request.POST, language=request.language)

        if not aid:
            aid_cookie = [value for key, value in request.COOKIES.items()
                          if '.'.join(('_pk_id',
                                       settings.SNM_TDC_HKFFW17_CS_ACCOUNT_ID
                                       )) in key]
            aid = (aid_cookie[0].split('.')[-1]
                   if len(aid_cookie) != 0 else None)

        if form.is_valid():
            contact = form.save(commit=False)

            with transaction.atomic():
                # NOTE: assume we have enough unused codes
                if contact.attend_jfs:
                    code_jfs = SignupCode.objects.filter(
                        used=False, is_jfs=True)[0]
                    code_jfs.used = True
                    code_jfs.save()
                    contact.signup_code_jfs = code_jfs.value
                if contact.attend_idg:
                    code_idg = SignupCode.objects.filter(
                        used=False, is_idg=True)[0]
                    code_idg.used = True
                    code_idg.save()
                    contact.signup_code_idg = code_idg.value

                contact_mgr = Contact.objects.filter(used_fb_mgr=True).count()

                if contact_mgr < settings.SNM_TDC_HKJF17_ALLOWED_FB_MGR_USER \
                    and ((request.language == 'chi' and contact.country == 'hk'
                          ) or request.language == 'eng'):
                    contact.is_show_mgr_btn = True

                fb_psid = form.cleaned_data['fb_psid']

                contact.language = request.language
                contact.aid = aid
                contact.is_mobile = mobile

                for i in xrange(5):
                    auth_str = binascii.hexlify(os.urandom(16))
                    if not Contact.objects.filter(auth_str=auth_str).exists():
                        contact.auth_str = auth_str
                        contact.save()
                        break
                contact.save()

                if fb_psid != '':
                    event_query = Event.objects.filter(
                        app_model_path='signup_mobile_tdc_hkjf17.Contact')

                    for event in event_query:
                        mark_registered(event, fb_psid)

                    data_ref = ('signup_mobile_tdc_hkjf17.Contact|%s'
                                % contact.auth_str)
                    create_mgr_signups(
                        settings.SNM_TDC_HKJF17_FB_PAGE_ID, fb_psid, data_ref)

            logger.debug('Contact received.', extra=logging_extra(request))
            return _redirect(next_view, {
                't': contact.auth_str,
                'cid': contact.email,
                'mgr': contact.is_show_mgr_btn,
            })
        else:
            logger.debug('Invalid form data.', extra=logging_extra(request))
            return render(request, template_name, {
                'form': form,
            })


@require_http_methods(['GET', 'POST'])
@mobile_enabled
@language_enabled
def signup_website(
        request, form_cls=SignupForm, network='website', mobile=False,
        template_name_website='signup_mobile_tdc_hkjf17/signup.html',
        template_name_wechat='signup_mobile_tdc_hkjf17/signup_wechat.html',
        template_name_mobile='signup_mobile_tdc_hkjf17/signup_mobile.html'):
    if network == 'website':
        template_name = (template_name_mobile
                         if mobile else template_name_website)
        next_view = 'snm_tdc_hkjf17_thanks_website'
    elif network == 'wechat':
        template_name = template_name_wechat
        form_cls = WechatSignupForm
        next_view = 'snm_tdc_hkjf17_thanks_wechat'
        request.language = SIMPLIFIED_CHINESE

    aid = request.GET.get(settings.CS_TRACKING_PARAMETER, None)

    if request.method == 'GET':
        form = form_cls(language=request.language)
        return render(request, template_name, {
            'CS_ACCOUNT_ID': settings.SNM_TDC_HKJF17_CS_ACCOUNT_ID,
            'CS_TRACKING_PATH': settings.SNM_TDC_HKJF17_URL_ROOT,
            'aid': aid,
            'is_cn': True if network == 'wechat' else False,
            'form': form,
            'network': network,
            'trackA': True,
        })

    elif request.method == 'POST':
        logger.debug(str(request.POST), extra=logging_extra(request))
        form = form_cls(data=request.POST, language=request.language)

        if not aid:
            aid_cookie = [value for key, value in request.COOKIES.items()
                          if '.'.join(('_pk_id',
                                       settings.SNM_TDC_HKFFW17_CS_ACCOUNT_ID
                                       )) in key]
            aid = (aid_cookie[0].split('.')[-1]
                   if len(aid_cookie) != 0 else None)

        if form.is_valid():
            contact = form.save(commit=False)

            with transaction.atomic():
                # NOTE: assume we have enough unused codes
                if contact.attend_jfs:
                    code_jfs = SignupCode.objects.filter(
                        used=False, is_jfs=True)[0]
                    code_jfs.used = True
                    code_jfs.save()
                    contact.signup_code_jfs = code_jfs.value
                if contact.attend_idg:
                    code_idg = SignupCode.objects.filter(
                        used=False, is_idg=True)[0]
                    code_idg.used = True
                    code_idg.save()
                    contact.signup_code_idg = code_idg.value

                contact_mgr = Contact.objects.filter(used_fb_mgr=True).count()

                if contact_mgr < settings.SNM_TDC_HKJF17_ALLOWED_FB_MGR_USER \
                    and ((request.language == 'chi' and contact.country == 'hk'
                          ) or request.language == 'eng'):
                    contact.is_show_mgr_btn = True

                fb_psid = form.cleaned_data['fb_psid']

                contact.language = request.language
                contact.aid = aid
                contact.is_mobile = mobile

                for i in xrange(5):
                    auth_str = binascii.hexlify(os.urandom(16))
                    if not Contact.objects.filter(auth_str=auth_str).exists():
                        contact.auth_str = auth_str
                        contact.save()
                        break

                if network == 'website':
                    contact.language = request.language
                elif network == 'twitter':
                    contact.language = ENGLISH
                    contact.is_twitter = True
                elif network == 'wechat':
                    contact.language = SIMPLIFIED_CHINESE
                    contact.is_wechat = True
                contact.save()

                if fb_psid != '':
                    event_query = Event.objects.filter(
                        app_model_path='signup_mobile_tdc_hkjf17.Contact')

                    for event in event_query:
                        mark_registered(event, fb_psid)

                    data_ref = ('signup_mobile_tdc_hkjf17.Contact|%s'
                                % contact.auth_str)
                    create_mgr_signups(
                        settings.SNM_TDC_HKJF17_FB_PAGE_ID, fb_psid, data_ref)

            logger.debug('Contact received.', extra=logging_extra(request))
            return _redirect(next_view, {
                't': contact.auth_str,
                'cid': contact.email,
                'mgr': contact.is_show_mgr_btn,
            })
        else:
            logger.debug('Invalid form data.', extra=logging_extra(request))
            return render(request, template_name, {
                'form': form,
                'network': network,
            })


@require_http_methods(['GET'])
@language_enabled
def thanks(
        request, mobile=False,
        template_name_desktop='signup_mobile_tdc_hkjf17/thanks.html',
        template_name_mobile='signup_mobile_tdc_hkjf17/thanks_mobile.html'):
    template_name = template_name_mobile if mobile else template_name_desktop

    auth_str = request.GET.get('t', None)
    cid = request.GET.get('cid', None)
    mgr = request.GET.get('mgr', None)

    if auth_str:
        pass_through_param = base64.urlsafe_b64encode(
            'signup_mobile_tdc_hkjf17.Contact|' + auth_str)
    else:
        pass_through_param = None
        mgr = False

    return render(request, template_name, {
        'CS_ACCOUNT_ID': settings.SNM_TDC_HKJF17_CS_ACCOUNT_ID,
        'CS_TRACKING_PATH': settings.SNM_TDC_HKJF17_URL_ROOT,
        'cid': cid,
        'gid': 'G-SIGNUP',
        'mgr': (mgr == 'True'),
        'pass_through_param': pass_through_param,
        'trackG': True,
    })


@require_http_methods(['GET'])
@mobile_enabled
@language_enabled
def thanks_website(
        request, network='website', mobile=False,
        template_name_website='signup_mobile_tdc_hkjf17/thanks.html',
        template_name_wechat='signup_mobile_tdc_hkjf17/thanks_wechat.html',
        template_name_mobile='signup_mobile_tdc_hkjf17/thanks_mobile.html'):
    if network == 'website':
        template_name = (template_name_mobile
                         if mobile else template_name_website)
    elif network == 'wechat':
        template_name = template_name_wechat
        request.language = SIMPLIFIED_CHINESE

    auth_str = request.GET.get('t', None)
    cid = request.GET.get('cid', None)
    mgr = request.GET.get('mgr', None)

    if auth_str:
        pass_through_param = base64.urlsafe_b64encode(
            'signup_mobile_tdc_hkjf17.Contact|' + auth_str)
    else:
        pass_through_param = None
        mgr = False

    return render(request, template_name, {
        'CS_ACCOUNT_ID': settings.SNM_TDC_HKJF17_CS_ACCOUNT_ID,
        'CS_TRACKING_PATH': settings.SNM_TDC_HKJF17_URL_ROOT,
        'cid': cid,
        'is_cn': True if network == 'wechat' else False,
        'gid': 'G-SIGNUP',
        'mgr': (mgr == 'True'),
        'network': network,
        'pass_through_param': pass_through_param,
        'trackG': True,
    })


def _redirect(view_name, query_dict):
    query_string = urllib.urlencode(query_dict)
    url = '%s?%s' % (reverse(view_name), query_string)
    return redirect(url)
