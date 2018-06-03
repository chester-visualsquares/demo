# -*- coding: utf-8 -*-
import base64
import logging

from django.utils import timezone

from common.utils import logging_extra
from fb_chatbot_event_tdc.models import (Event, FacebookPage, FacebookUser,
                                         RegisterReminderList)
from fb_chatbot_event_tdc import utils
from pymessenger import Element


logger = logging.getLogger('django.request.logger')


HELP_MESSAGE = (u'This is an auto-reply message. '
                u'For enquiries, please email exhibitions@hktdc.org or call '
                u'our Customer Service Line (852) 1830 668. \n'
                u'這是自動回覆的訊息。如有查詢，請電郵至 exhibitions@hktdc.org'
                u'或撥打我們的顧客服務熱線 (852) 1830 668。')


def post_text_message(fb_page, receiver, message):
    bot = utils.init_bot(fb_page)
    for i in xrange(3):
        text_response = bot.send_text_message(receiver, message)
        if 'error' not in text_response:
            break
    status = 'Error' if 'error' in text_response else 'Success'
    msg_tmpl = u'Receiver: {0}, Message: {1}, Status: {2}, Response: {3}'
    utils.save_delivered_message(fb_page, receiver, message, text_response)
    logger.debug(msg_tmpl.format(receiver, message, status, text_response),
                 extra=logging_extra())
    return status


def post_button_message(fb_page, receiver, text, button):
    bot = utils.init_bot(fb_page)
    for i in xrange(3):
        button_response = bot.send_button_message(receiver, text, button)
        if 'error' not in button_response:
            break
    status = 'Error' if 'error' in button_response else 'Success'
    msg_tmpl = (u'Receiver: {0}, Text: {1}, Button: {2},'
                u' Status: {3}, Response: {4}')
    utils.save_delivered_message(fb_page, receiver, '%s %s' % (text, button),
                                 button_response)
    logger.debug(msg_tmpl.format(receiver, text, button, status,
                                 button_response), extra=logging_extra())
    return status


def post_generic_message(fb_page, receiver, elements):
    bot = utils.init_bot(fb_page)
    for i in xrange(3):
        generic_msg_response = bot.send_generic_message(receiver, elements)
        if 'error' not in generic_msg_response:
            break
    status = 'Error' if 'error' in generic_msg_response else 'Success'
    msg_tmpl = u'Receiver: {0}, Elements: {1}, Status: {2}, Response: {3}'
    logger.debug(msg_tmpl.format(receiver, elements, status,
                                 generic_msg_response), extra=logging_extra())
    return status


def handle_optin(messaging):
    fb_page = FacebookPage.objects.get(fbid=messaging['recipient']['id'])
    ref_decoded = base64.urlsafe_b64decode(
        str(messaging['optin']['ref']))
    fb_user_id = messaging['sender']['id']
    signup_query, unique = utils.signup_send_to_messenger(
        fb_page,
        messaging['sender']['id'],
        ref_decoded)

    if signup_query and not unique:
        for signup in signup_query:
            text, button = utils.another_signup_button(signup)
            post_button_message(
                fb_page, fb_user_id, text, button)
    elif signup_query:
        for signup in signup_query:
            utils.mark_registered(signup.event, fb_user_id)
        send_thank_you_message(fb_page, fb_user_id, signup_query)


def create_mgr_signups(fb_page_id, fb_user_id, data_ref):
    fb_page = FacebookPage.objects.get(fbid=fb_page_id)
    signup_query, unique = utils.signup_send_to_messenger(
        fb_page, fb_user_id, data_ref)
    send_thank_you_message(
        fb_page, fb_user_id, signup_query)


def send_thank_you_message(fb_page, fb_user_id, signup_query):
    thank_you_text = {
        'eng': ('Thank you for reserving your admission badge to the '
                'following event(s):'),
        'chi': u'多謝閣下預留免費入場證參觀以下展覽：'
    }
    ref_num_text = {
        'eng': ('Please show your reference number at "Buyer Registration'
                ' Counter" to complete the registration process and redeem '
                'the admission badge. Thank You!'
                ),
        'chi': u'請到會場的「買家登記處」出示登記參考編號，以完成登記程序及索取免費入場證。'
    }
    share_text = {
        'eng': ('You can register again or share the event with your friends.'
                ),
        'chi': u'您可以為下一位來賓登記，或與您的好友分享這個展覽。'
    }
    lang = signup_query[0].fb_user.language
    post_text_message(
        fb_page, fb_user_id,
        thank_you_text.get(lang, 'eng'))
    for signup in signup_query:
        text, button = utils.more_info_button(signup, lang)
        post_button_message(fb_page, signup.fb_user.fbid, text, button)
    post_text_message(
        fb_page, signup.fb_user.fbid,
        ref_num_text.get(lang, 'eng'))

    elements = []
    for signup in signup_query:
        signup_page_url_str = {
            'eng': signup.event.signup_page_url_str + '&lang=eng',
            'chi': signup.event.signup_page_url_str + '&lang=chi',
        }
        title = signup.event.name_chi if lang == 'chi' else signup.event.name

        element = Element(title=title,
                          image_url=signup.event.event_image_url_str,
                          subtitle=share_text.get(lang, 'eng'),
                          item_url=signup_page_url_str.get(lang, 'eng'),
                          buttons=utils.after_registration_button(
                              signup.event, lang)
                          )

        elements.append(element)
    post_generic_message(fb_page, fb_user_id,
                         elements)


def handle_message(messaging):
    if 'is_echo' in messaging['message']:
        if messaging['message']['is_echo']:
            return

    fb_page = FacebookPage.objects.get(fbid=messaging['recipient']['id'])
    fb_user = FacebookUser.objects.filter(
        fb_page=fb_page, fbid=messaging['sender']['id'])
    if fb_user.exists():
        utils.save_received_message(fb_page, messaging)
        if not fb_user.first().auto_replied:
            post_text_message(fb_page, messaging['sender']['id'], HELP_MESSAGE)
            fb_user.update(auto_replied=True)


def handle_delivery(messaging):
    fb_page = FacebookPage.objects.get(fbid=messaging['recipient']['id'])
    utils.save_message_deliveries(
        fb_page, messaging['sender']['id'], messaging['delivery'])


def handle_postback(messaging):
    fb_page = FacebookPage.objects.get(fbid=messaging['recipient']['id'])
    received_postback = utils.save_received_postback(fb_page, messaging)
    payload = messaging['postback']['payload']

    if payload.split('.')[0] != 'HELP_MESSAGE':
        fb_user = FacebookUser.objects.get_or_create(
            fb_page=fb_page, fbid=messaging['sender']['id'])[0]
        lang = fb_user.language
    else:
        fb_user = None
        lang = 'eng'

    if payload.split('.')[0] == 'REGISTER_EVENT':
        lang = payload.split('.')[1]
        fb_user.language = lang
        fb_user.save()
        RegisterReminderList.objects.create(
            fb_user=fb_user,
            event=Event.objects.get(pk=payload.split('.')[2]),
        )

        title_text = {
            'eng': 'Reserve Your Free Admission Badge: %s',
            'chi': u'預留免費入場證：%s'
        }
        subtitle_text = {
            'eng': 'Tap "Reserve Now" to begin.',
            'chi': u'按「現在預留」開始進行登記。'
        }
        elements = []
        for event_pk in payload.split('.')[2:]:
            event = Event.objects.get(pk=event_pk)
            signup_page_url_str = {
                'eng': event.signup_page_url_str + '&lang=eng',
                'chi': event.signup_page_url_str + '&lang=chi',
            }
            title = (title_text.get('chi') % event.name_chi if lang == 'chi'
                     else title_text.get('eng') % event.name)
            element = Element(
                title=title,
                image_url=event.event_image_url_str,
                subtitle=subtitle_text.get(lang, 'eng'),
                item_url=signup_page_url_str.get(lang, 'eng'),
                buttons=utils.registration_button(event, lang)
            )

            elements.append(element)
        post_generic_message(fb_page, messaging['sender']['id'],
                             elements)

    if payload.split('.')[0] == 'REMINDER_REFERENCE_NUM':
        signup_query = utils.get_signup_query(
            fb_page, messaging['sender']['id'], payload.split('.')[1])
        status = ''

        signup_info_text = {
            'eng': ('{0} - Your signup information\n'
                    'First Name: {1}\n'
                    'Last Name: {2}\n'
                    'Reference No.: {3}'),
            'chi': (u'{0} - 您的登記資料\n'
                    u'姓氏: {2}\n'
                    u'名字: {1}\n'
                    u'參考編號: {3}')
        }
        terms_text = {
            'eng': ('For Security reason, your passport or HK identity card '
                    'will be required to collect your admission badge. With '
                    'our enhanced security measures, all buyers are required '
                    'to present a valid photo bearing identity document for '
                    'on-site veification before entering the hall venues.'),
            'chi': (u'基於保安考慮，請攜帶您的護照或香港身份證領取入場證。所有參觀人士也會'
                    u'被要求檢查身份證明文件上的近照，以茲識別。')
        }

        for signup in signup_query:
            event_name = (signup.event.name_chi if lang == 'chi'
                          else signup.event.name)
            signup_info_message = signup_info_text.get(lang, 'eng').format(
                event_name,
                signup.contact_object.first_name,
                signup.contact_object.last_name,
                signup.signup_code
            )
            status = post_text_message(fb_page, fb_user.fbid,
                                       signup_info_message)
        post_text_message(
            fb_page, fb_user.fbid, terms_text.get(lang, 'eng'))
        if status == 'Success':
            received_postback.responded = True
            received_postback.save()

    if payload.split('.')[0] == 'WELCOME_GIFT':
        event = Event.objects.get(pk=payload.split('.')[1])
        text = event.gift_message if lang == 'eng' else event.gift_message_chi
        pre_gift_text = {
            'eng': ('The fair souvenirs are still being arranged at '
                    'the moment, please check back later for more information.'
                    ),
            'chi': u'感謝您對本展覽的興趣，我們正在準備閣下的精美禮品，請稍後再次查看。'
        }

        if text == '':
            post_text_message(fb_page, messaging['sender']['id'],
                              pre_gift_text.get(lang, 'eng'))
        else:
            post_text_message(fb_page, messaging['sender']['id'], text)

            text, button = utils.gift_message_button(
                payload.split('.')[1], lang)
            status = post_button_message(
                fb_page, messaging['sender']['id'], text, button)
            if status == 'Success':
                received_postback.responded = True
                received_postback.save()

    elif payload == 'GIFT_TERMS_COND':
        text_messages = utils.gift_terms_messages(lang)
        status = ''
        for text in text_messages:
            status = post_text_message(
                fb_page, messaging['sender']['id'], text)
        if status == 'Success':
            received_postback.responded = True
            received_postback.save()

    elif payload.split('.')[0] == 'GET_ALL_SIGNUP':
        signup_query = utils.get_all_signup_query(fb_page,
                                                  messaging['sender']['id'])
        event_query = set(signup.event for signup in signup_query
                          if signup.event.end_date > timezone.now().date())

        subtitle_text = {
            'eng': 'Tap for more details',
            'chi': u'按此查看更多資訊'
        }
        instruct_text = {
            'eng': ('If you need your reference number again, tap the '
                    '"Reference Number" button. Learn how to redeem fair '
                    'souvenirs by tapping the "Fair Souvenirs" button.'),
            'chi': (u'想查看您的參考編號? 請按「我的參考編號」。'
                    u'想查看領取的禮品及方法? 請按「領取精美禮品」。')
        }
        no_reg_text = {
            'eng': "You didn't register any upcoming events.",
            'chi': u'您還未注冊任何即將開始的香港貿發局展覽。'
        }

        elements = []
        status = ''
        if event_query:
            for event in event_query:
                event_page_url_str = {
                    'eng': event.event_page_url_str,
                    'chi': event.event_page_url_str.replace('-en', '-tc')
                }
                title = event.name_chi if lang == 'chi' else event.name

                element = Element(title=title,
                                  image_url=event.event_image_url_str,
                                  subtitle=subtitle_text.get(lang, 'eng'),
                                  item_url=event_page_url_str.get(lang, 'eng'),
                                  buttons=utils.view_event_buttons(event, lang)
                                  )
                elements.append(element)
            status = post_generic_message(fb_page, fb_user.fbid,
                                          elements)
            post_text_message(
                fb_page, messaging['sender']['id'],
                instruct_text.get(lang, 'eng'))
        else:
            status = post_text_message(
                fb_page, messaging['sender']['id'],
                no_reg_text.get(lang, 'eng'))
        if status == 'Success':
            received_postback.responded = True
            received_postback.save()

    elif payload.split('.')[0] == 'HELP_MESSAGE':
        status = post_text_message(fb_page,
                                   messaging['sender']['id'], HELP_MESSAGE)
        if status == 'Success':
            received_postback.responded = True
            received_postback.save()

    else:
        pass


def no_operation(messaging):
    pass
