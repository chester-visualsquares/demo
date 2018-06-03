# -*- coding: utf-8 -*-
import base64
import logging
import pytz
import requests

from datetime import datetime
from django.apps import apps
from django.db import transaction

from fb_chatbot_event_tdc.models import (DeliveredMessage,
                                         DeliveryPostback, Event,
                                         FacebookUser,
                                         ReceivedMessage,
                                         ReceivedPostback,
                                         RegisterReminderList,
                                         Signup)
from pymessenger.bot import Bot

logger = logging.getLogger('django.request.logger')


def init_bot(fb_page):
    bot = Bot(fb_page.access_token, api_version='2.8')
    return bot


@transaction.atomic()
def save_received_message(fb_page, message):
    fb_user_id = message['sender']['id']
    fb_user = FacebookUser.objects.get_or_create(
        fb_page=fb_page, fbid=fb_user_id)[0]
    timestamp = message['timestamp']
    mid = message['message']['mid']
    seq = message['message']['seq']
    message = message['message']
    received_message = ReceivedMessage.objects.get_or_create(
        fb_page=fb_page,
        fb_user=fb_user,
        timestamp=timestamp,
        mid=mid,
        seq=seq,
        message=message)[0]
    return received_message


@transaction.atomic()
def save_delivered_message(fb_page, fb_user_id, message, text_response):
    fb_user = FacebookUser.objects.get_or_create(
        fb_page=fb_page, fbid=fb_user_id)[0]
    try:
        mid = text_response['message_id']
    except KeyError:
        mid = None

    return DeliveredMessage.objects.create(
        fb_page=fb_page, fb_user=fb_user, message=message,
        response=text_response, mid=mid
    )


@transaction.atomic()
def save_received_postback(fb_page, messaging):
    fb_user = FacebookUser.objects.get_or_create(
        fb_page=fb_page,
        fbid=messaging['sender']['id'])[0]
    return ReceivedPostback.objects.create(
        fb_page=fb_page, fb_user=fb_user, timestamp=messaging['timestamp'],
        postback=messaging['postback'],
    )


def is_char_limit(text_field, char_limit):
    if len(text_field) > char_limit or len(text_field) == 0:
        logger.debug('Sending  "{}" > {} or 0 characters.'.format(
            text_field, char_limit))
        return False


def is_element_limit(dict_list, element_limit):
    if len(dict_list) > element_limit:
        logger.debug('Sending  "{}" > {} or 0 elements.'.format(
                     dict_list, element_limit))
        return False


def get_user_details(fb_page, fb_user_id):
    user_details_params = {
        'fields': 'first_name, last_name, '
        'profile_pic, locale, timezone, gender',
        'access_token': fb_page.access_token}
    user_details_url = 'https://graph.facebook.com/v2.8/%s' % fb_user_id
    user_details_dict = requests.get(user_details_url,
                                     user_details_params).json()
    return user_details_dict


def get_signup_query(fb_page, fb_user_id, event_id):
    fb_user = FacebookUser.objects.get_or_create(
        fb_page=fb_page, fbid=fb_user_id)[0]
    signup_query = Signup.objects.filter(event__id=event_id,
                                         fb_user=fb_user)

    return signup_query


def get_all_signup_query(fb_page, fb_user_id):
    fb_user = FacebookUser.objects.get_or_create(
        fb_page=fb_page, fbid=fb_user_id)[0]
    signup_query = Signup.objects.filter(fb_user=fb_user)

    return signup_query


# This function handles users use "Send to Messenger" button.
# Case 1: New signup, click the button
#             return (new signup object, unique=True)
#
# Case 2: Existing signup, click the button by same FB user(signup.fb_user)
#             return (existing signup object, unique=True)
#
# Case 3: Existing signup, click the button by another FB user(signup.fb_user)
#             return (existing signup object, unique=False)
#
# Case 4: Non-existing event or signup, click the button by any FB user
#             return (None, None)
#
def signup_send_to_messenger(fb_page, fb_user_id, data_ref):
    fb_user = FacebookUser.objects.get_or_create(
        fb_page=fb_page, fbid=fb_user_id)[0]
    fb_user.unsubscribe = False
    fb_user.auto_replied = False
    app_model_path = data_ref.split('|')[0]
    auth_str = data_ref.split('|')[1]

    contact_query = apps.get_model(
        *app_model_path.split('.')).objects.filter(auth_str=auth_str)
    contact = contact_query.first()
    if not contact:
        logger.debug("Invaild contact. This contact doesn't exist")
        return None, None

    fb_user.language = contact.language
    if fb_user.language == 'sc':
        fb_user.language = 'chi'
    fb_user.save()

    signup_query = Signup.objects.filter(
        contact=app_model_path + '|' + str(contact.pk))
    if signup_query.exists() and str(
            signup_query.first().fb_user.fbid) != fb_user_id:
        return signup_query, False

    event_query = Event.objects.filter(
        fb_page=fb_page, app_model_path=app_model_path)
    if not event_query.exists():
        logger.debug("Invaild app_model_path. This event doesn't exist")
        return None, None

    contact.used_fb_mgr = True
    contact.save()

    for event in event_query:
        contact_object = contact_query.filter(**event.contact_filters_dict)
        signup_code = getattr(contact, event.signup_code_attr, None)
        if contact_object:
            Signup.objects.get_or_create(
                fb_user=fb_user,
                contact=app_model_path + '|' + str(contact.pk),
                event=event,
                signup_code=signup_code)
    else:
        signup_query = Signup.objects.filter(
            contact=app_model_path + '|' + str(contact.pk))
        return signup_query, True


def mark_registered(event, fb_user_id):
    fb_user = FacebookUser.objects.filter(
        fb_page=event.fb_page, fbid=fb_user_id).first()
    if fb_user:
        reminder_query = RegisterReminderList.objects.filter(
            event=event, fb_user=fb_user, registered=False)
        reminder_query.update(registered=True)


def registration_button(event, lang):
    signup_page_url_str = {
        'eng': event.signup_page_url_str + '&lang=eng',
        'chi': event.signup_page_url_str + '&lang=chi',
    }
    button_title = {
        'eng': 'Register Now',
        'chi': u'現在預留',
    }
    button = [
        {
            'type': 'web_url',
            'url': signup_page_url_str.get(lang, 'eng'),
            'title': button_title.get(lang, 'eng'),
            'webview_height_ratio': 'full',
            'messenger_extensions': True,
        },
    ]
    return button


def more_info_button(signup, lang):
    text_eng = (
        '{0}\n'
        'Venue: {3}\n'
        'Date: {1:%b} {1.day} - {2:%b} {2.day}, {1:%Y}\n'
        'Reference No.: {4}'
    ).format(signup.event.name,
             signup.event.start_date,
             signup.event.end_date,
             signup.event.venue,
             signup.signup_code
             )

    text_chi = (
        u'{0}\n'
        u'地點：{3}\n'
        u'日期：{1:%Y}年{1.month}月{1.day}日至{2.month}月{2.day}日\n'
        u'參考編號：{4}'
    ).format(signup.event.name_chi,
             signup.event.start_date,
             signup.event.end_date,
             signup.event.venue_chi,
             signup.signup_code
             )
    button_title = {
        'eng': 'Event Details',
        'chi': u'展覽詳情'
    }
    event_page_url_str = {
        'eng': signup.event.event_page_url_str,
        'chi': signup.event.event_page_url_str.replace('-en', '-tc')
    }

    button = [
        {
            'type': 'web_url',
            'url': event_page_url_str.get(lang, 'eng'),
            'title': button_title.get(lang, 'eng')
        },
    ]
    text = text_eng if lang == 'eng' else text_chi
    return text, button


def after_registration_button(event, lang):
    title = {
        'eng': ('Register now to reserve your FREE '
                'admission badge for this event!'),
        'chi': u'現在預留您的免費入場證！'
    }
    subtitle = {
        'eng': ('You have been invited to attend this HKTDC event.'),
        'chi': u'您的好友誠邀您參與這個由香港貿發局舉辦的展覽。'
    }
    rg_now_button = {
        'eng': 'Register Now',
        'chi': u'現在注冊'
    }
    rg_again_button = {
        'eng': 'Register Again',
        'chi': u'再次注冊'
    }
    signup_page_url_str = {
        'eng': event.signup_page_url_str + '&lang=eng',
        'chi': event.signup_page_url_str + '&lang=chi',
    }
    share_elements = [
        {
            'title': title.get(lang, 'eng'),
            'subtitle': subtitle.get(lang, 'eng'),
            'image_url': event.event_image_url_str,
            'default_action': {
                'type': 'web_url',
                'url': signup_page_url_str.get(lang, 'eng'),
                'webview_height_ratio': 'full',
            },
            'buttons': [
                {
                    'type': 'web_url',
                    'url': signup_page_url_str.get(lang, 'eng'),
                    'title': rg_now_button.get(lang, 'eng'),
                    'webview_height_ratio': 'full',
                }
            ]
        }
    ]

    button = [
        {
            'type': 'web_url',
            'url': signup_page_url_str.get(lang, 'eng'),
            'title': rg_again_button.get(lang, 'eng'),
            'webview_height_ratio': 'full',
            'messenger_extensions': True,
        },
        {
            'type': 'element_share',
            'share_contents': {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'generic',
                        'elements': share_elements}
                }
            }
        }
    ]
    return button


def switch_fb_account_button(signup):
    switch_string = base64.urlsafe_b64encode(
        '|'.join(('SWITCH_ACC', signup.event.app_model_path,
                  signup.contact_object.auth_str))
    )

    text = (
        'We are going to unlink the signup with previous Facebook account '
        'since 1 signup can only be linked with 1 Facebook account.'
        'Do you want to use this Facebook account to subscribe our messages '
        'instead?'
    )
    button = [
        {
            'type': 'postback',
            'title': 'Yes',
            'payload': switch_string
        },
        {
            'type': 'postback',
            'title': 'No',
            'payload': base64.urlsafe_b64encode('NOT_SWITCH_ACC')
        },
    ]
    return text, button


def another_signup_button(signup):
    text = (
        'It appears that your registration has been linked to another Facebook'
        ' account. If you want to receive your registration confirmation on '
        'this Facebook account, please register for the event again. Remember '
        'to sign in to this account when you tap "Send to Messenger" at the '
        'Thank You page.'
        u'您已經以另一個 Facebook 帳戶成功登記。如果您想用這個 Facebook 帳戶接收注冊資訊，'
        u'請重新登記。請緊記登入這個帳戶後才在注冊完成頁面上按 "Send to Messenger"。'
    )
    button = [
        {
            'type': 'web_url',
            'url': signup.event.signup_page_url_str,
            'title': u'再次注冊 Register Again',
            'webview_height_ratio': 'full',
            'messenger_extensions': True,
        },
    ]
    return text, button


def reminder_message_button(fb_user):
    initial_text = {
        'eng': ('The following HKTDC event(s) that you have registered '
                'for will be happening soon.'),
        'chi': u'以下由香港貿發局舉辦的展覽即將舉行的：'
    }

    instruct_text = {
        'eng': ('Tap the button below to get more details about '
                'your registration(s) and the event(s).'),
        'chi': u'按以下的鍵可參閱登記資料或展覽詳情。'
    }

    see_more_button = {
        'eng': 'See my events',
        'chi': u'查看我已登記的展覽'
    }

    event_set = set(signup_obj.event for signup_obj in Signup.objects.filter(
        fb_user=fb_user,
        event__end_date__gte=datetime.now(pytz.timezone('Asia/Hong_Kong'))
    ))

    if fb_user.language == 'chi':
        event_text = ((u'{0} ({1.month}月{1.day}日至{2.month}月{2.day}日)').format(
            event.name_chi,
            event.start_date,
            event.end_date
        ) for event in event_set)
    else:
        event_text = (('{0} ({1:%b} {1.day} - {2:%b} {2.day})').format(
            event.name,
            event.start_date,
            event.end_date
        ) for event in event_set)

    text = '\n'.join((initial_text.get(fb_user.language, 'eng'),
                      '\n'.join(event_text),
                      instruct_text.get(fb_user.language, 'eng')))

    button = [
        {
            'type': 'postback',
            'title': see_more_button.get(fb_user.language, 'eng'),
            'payload': 'GET_ALL_SIGNUP'
        },
    ]
    return text, button


def reigster_reminder_message_button(event, lang):
    text = {
        'eng': ('Are you still interested in attending the %s? Remember '
                'to sign up soon to secure your free admission badge!'
                % event.name),
        'chi': (u'您是否仍然想參加%s？記得盡快優先登記，預留免費入場證！'
                % event.name_chi)
    }

    register_button_text = {
        'eng': 'Register Now',
        'chi': u'現在注冊'
    }
    more_info_button_text = {
        'eng': 'More Information',
        'chi': u'更多資料'
    }
    event_page_url_str = {
        'eng': event.event_page_url_str,
        'chi': event.event_page_url_str.replace('-en', '-tc')
    }
    signup_page_url_str = {
        'eng': event.signup_page_url_str + '&lang=eng',
        'chi': event.signup_page_url_str + '&lang=chi',
    }
    button = [
        {
            'type': 'web_url',
            'title': register_button_text.get(lang, 'eng'),
            'url': signup_page_url_str.get(lang, 'eng'),
            'webview_height_ratio': 'full',
            'messenger_extensions': True,
        },
        {
            'type': 'web_url',
            'title': more_info_button_text.get(lang, 'eng'),
            'url': event_page_url_str.get(lang, 'eng'),
        },
    ]
    return text.get(lang, 'eng'), button


def gift_message_button(event_id, lang):
    title_text = {
        'eng': 'Terms and Conditions apply.',
        'chi': u'您可以查看有關條款及細則。'
    }
    button_text = {
        'eng': 'Terms and Conditions',
        'chi': u'條款及細則'
    }
    button = [
        {
            'type': 'postback',
            'title': button_text.get(lang, 'eng'),
            'payload': 'GIFT_TERMS_COND'
        }
    ]
    return title_text.get(lang, 'eng'), button


def gift_terms_messages(lang):
    gift_text = {
        'eng': (
            '- Visitors who are redeeming the gift via confirmation on '
            'Facebook Messenger/email are not entitled to redeem the gift via'
            ' "Like/Follow 2 Social Media Accounts or more to redeem gifts" '
            'at the social media counter. \n'
            '- Visitor can only choose one of the redemption methods to '
            'redeem his/her gift. Each visitor is entitled to only one gift.\n'
            '- All gifts are distributed on a first-come-first-served '
            'basis while supplies last.\n...'
            '- Each buyer can redeem only 1 souvenir.\n'
            '- You must present all the confirmation messages and '
            'buyer badges when making collection by authorization.\n'
            '- Only a maximum of 1 souvenir can be collected by '
            'authorization.\n'
            "- In the case of any dispute, HKTDC's determination "
            'shall be final.\n'
        ).split('...'),
        'chi': (u'- 凡以此 Facebook 訊息/電郵副本成功換領禮品之買家，並不享有'
                u'「即場關注兩個以上社交媒體帳號可換領禮品」之權利。\n'
                u'- 買家只可選擇其中一種換領方法換領禮品。\n'
                u'- 所有禮物按先到先得形式派發，換完即止。\n'
                u'- 每位買家只可換領以上禮品其中一項。\n'
                u'- 如代領，須出示所有 Facebook 訊息/電郵副本和買家證，方可領取禮物。\n'
                u'- 不可代領超過1份禮物。\n'
                u'- 如有任何爭議，主辦單位保留最終決定權。').split('...')
    }
    return gift_text.get(lang, 'eng')


def view_event_buttons(event, lang):
    event_title = {
        'eng': 'Event Page',
        'chi': u'展覽詳情'
    }
    ref_num_title = {
        'eng': 'Reference number',
        'chi': u'我的參考編號'
    }
    souvenir_title = {
        'eng': 'Fair Souvenirs',
        'chi': u'領取精美禮品'
    }
    event_page_url_str = {
        'eng': event.event_page_url_str,
        'chi': event.event_page_url_str.replace('-en', '-tc')
    }

    button = [
        {
            'type': 'web_url',
            'url': event_page_url_str.get(lang, 'eng'),
            'title': event_title.get(lang, 'eng')
        },
        {
            'type': 'postback',
            'title': ref_num_title.get(lang, 'eng'),
            'payload': u'REMINDER_REFERENCE_NUM.' + str(event.id)
        },
        {
            'type': 'postback',
            'title': souvenir_title.get(lang, 'eng'),
            'payload': 'WELCOME_GIFT.' + str(event.id)
        },
    ]
    return button


@transaction.atomic()
def save_message_deliveries(fb_page, fb_user_id, delivery_message):
    fb_user = FacebookUser.objects.filter(fb_page=fb_page,
                                          fbid=fb_user_id).first()
    if fb_user and 'mids' in delivery_message:
        for mid in delivery_message['mids']:
            DeliveryPostback.objects.create(
                fb_page=fb_page, fb_user=fb_user,
                mid=mid, watermark=delivery_message['watermark'],
                seq=delivery_message['seq'])
            DeliveredMessage.objects.filter(
                fb_user=fb_user, mid=mid).update(acknowledged=True)
