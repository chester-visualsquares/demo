import json
import logging
import requests
import urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import (HttpResponse, HttpResponseForbidden,
                         JsonResponse)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView


from common.utils import logging_extra
from fb_chatbot_event_tdc import utils
from fb_chatbot_event_tdc.decorators import (client_hktdc_required,
                                             fb_page_required)
from fb_chatbot_event_tdc.forms import BroadcastForm, SendReminderForm
from fb_chatbot_event_tdc.messaging import (post_text_message,
                                            post_button_message,
                                            handle_optin,
                                            handle_message,
                                            handle_postback,
                                            handle_delivery,
                                            no_operation)
from fb_chatbot_event_tdc.models import Event, FacebookPage, Signup


logger = logging.getLogger('django.request.logger')


class MessengerView(generic.View):

    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token']  \
                == settings.CHATBOT_EVENT_TDC_VERIFY_TOKEN:
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            logger.debug('Failed validation. '
                         'Make sure the validation tokens match.',
                         extra=logging_extra(self.request))
            return HttpResponseForbidden()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        logger.debug(incoming_message, extra=logging_extra(self.request))
        if incoming_message['object'] != 'page':
            return HttpResponse()

        for entry in incoming_message['entry']:
            for messaging in entry.get('messaging', []):
                self.handle_messaging(messaging)
        return HttpResponse()

    def handle_messaging(self, messaging):
        messaging_map = {
            'optin': handle_optin,
            'message': handle_message,
            'postback': handle_postback,
            'delivery': handle_delivery,
            'read': no_operation,
        }
        for key, func in messaging_map.items():
            if key in messaging:
                func(messaging)
                break
        else:
            logger.debug('Webhook received unknown '
                         'messaging event: %s', messaging,
                         extra=logging_extra(self.request))


class FBAuthenticationView(generic.View):

    def get(self, request, *args, **kwargs):
        url = request.build_absolute_uri(
            reverse('fb_chatbot_event_tdc_fb_auth_code'))
        return render(request, 'fb_chatbot_event_tdc/fb_authentication.html',
                      {'redirect_uri': url, })

    @method_decorator(login_required(login_url='/hktdc-bot-trial/login/'))
    @method_decorator(client_hktdc_required)
    def dispatch(self, *args, **kwargs):
        return super(FBAuthenticationView, self).dispatch(*args, **kwargs)


class FBAuthenticationCodeView(generic.View):

    def get(self, request, *args, **kwargs):
        params_dict = {
            'client_id': settings.CHATBOT_EVENT_TDC_FB_APP_ID,
            'client_secret': settings.CHATBOT_EVENT_TDC_FB_APP_ACCESS_TOKEN,
            'code': request.GET.get('code', None),
            'redirect_uri': request.build_absolute_uri(
                reverse('fb_chatbot_event_tdc_fb_auth_code')),
        }

        user_token_url = 'https://graph.facebook.com/v2.10/oauth/access_token'
        user_token_dict = requests.get(user_token_url, params_dict).json()
        if 'error' in user_token_dict:
            return _redirect('fb_chatbot_event_tdc_fb_auth', {
                'error_message': 'We cannot get the authentication from you.',
            })
        else:
            user_token = user_token_dict.get('access_token')
            return _redirect('fb_chatbot_event_tdc_fb_auth_page', {
                'user_token': user_token, })

    @method_decorator(login_required(login_url='/hktdc-bot-trial/login/'))
    @method_decorator(client_hktdc_required)
    def dispatch(self, *args, **kwargs):
        return super(FBAuthenticationCodeView, self).dispatch(*args, **kwargs)


class FBAuthPages(generic.View):

    def get(self, request, *args, **kwargs):
        page_token_url = 'https://graph.facebook.com/v2.10/me/accounts'
        user_token = request.GET.get('user_token', None),
        page_token_dict = requests.get(
            page_token_url, {'access_token': user_token, }).json()
        request.session['user_token'] = user_token
        page_list = page_token_dict.get('data')

        if not page_list:
            url = request.build_absolute_uri(
                reverse('fb_chatbot_event_tdc_fb_auth_code'))
            return render(
                request, 'fb_chatbot_event_tdc/fb_authentication.html',
                {'error_message': 'We cannot get the authentication from you.',
                 'redirect_uri': url,
                 })

        return render(request, 'fb_chatbot_event_tdc/fb_auth_page_token.html',
                      {'page_list': page_list})

    def post(self, request, *args, **kwargs):
        page_token_url = 'https://graph.facebook.com/v2.10/me/accounts'
        user_token = request.session.get('user_token')
        page_token_dict = requests.get(
            page_token_url, {'access_token': user_token, }).json()
        page_list = page_token_dict.get('data')
        page_id = request.POST.get('page_id')
        page = [page for page in page_list if page.get('id') == page_id][0]

        bot_subs_url = 'https://graph.facebook.com/v2.10/me/subscribed_apps'
        bot_subs_status = requests.post(
            bot_subs_url, {'access_token': page.get('access_token'), }).json()
        if bot_subs_status.get('success'):
            page_object = FacebookPage.objects.get_or_create(fbid=page_id)[0]
            page_object.access_token = page.get('access_token')
            page_object.save()
            return render(request, 'fb_chatbot_event_tdc/fb_auth_status.html',
                          {'page_name': page.get('name'), })

        else:
            error_message = 'Failed to subscribe the Page %s to the Bot'
            return render(request,
                          'fb_chatbot_event_tdc/fb_auth_page_token.html',
                          {'page_list': page_list,
                           'error_message': error_message % page.get('name')})

    @method_decorator(login_required(login_url='/hktdc-bot-trial/login/'))
    @method_decorator(client_hktdc_required)
    def dispatch(self, *args, **kwargs):
        return super(FBAuthPages, self).dispatch(*args, **kwargs)


class FBAuthSuccessView(generic.View):

    def get(self, request, *args, **kwargs):
        message = request.GET.get('message', None)
        return render(request, 'fb_chatbot_event_tdc/fb_auth_status.html',
                      {'message': message}, )

    @method_decorator(login_required(login_url='/hktdc-bot-trial/login/'))
    @method_decorator(client_hktdc_required)
    def dispatch(self, *args, **kwargs):
        return super(FBAuthSuccessView, self).dispatch(*args, **kwargs)


class BroadcastView(FormView):
    template_name = 'fb_chatbot_event_tdc/broadcast.html'
    form_class = BroadcastForm

    def form_valid(self, form):
        event = form.cleaned_data['event']
        text = form.cleaned_data['message']
        for signup in Signup.objects.filter(event=event,
                                            fb_user__unsubscribe=False):
            status = post_text_message(event.fb_page,
                                       signup.fb_user.fbid, text)
            if status == 'Success':
                messages.success(
                    self.request,
                    ' '.join(('Message "', text, '" has been sent to',
                              str(signup.fb_user.fbid))))
            else:
                messages.error(self.request,
                               ' '.join(('Failed to send message to',
                                         str(signup.fb_user.fbid))))
        return super(BroadcastView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(BroadcastView, self).get_context_data(**kwargs)
        context['fb_page'] = self.fb_page
        return context

    def get_form_kwargs(self):
        kwargs = super(BroadcastView, self).get_form_kwargs()
        kwargs['fb_page_id'] = self.kwargs['fb_page_id']
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy('fb_chatbot_event_tdc_broadcast_status',
                            kwargs={'fb_page_id': self.fb_page.pk})

    @method_decorator(staff_member_required)
    @fb_page_required
    def dispatch(self, *args, **kwargs):
        return super(BroadcastView, self).dispatch(*args, **kwargs)


class BroadcastStatusView(generic.View):

    def get(self, request, *args, **kwargs):
        fb_page = self.fb_page
        return render(request,
                      'fb_chatbot_event_tdc/broadcast_status.html',
                      {'fb_page': fb_page})

    @method_decorator(staff_member_required)
    @fb_page_required
    def dispatch(self, *args, **kwargs):
        return super(BroadcastStatusView, self).dispatch(*args, **kwargs)


class SendReminderView(FormView):
    template_name = 'fb_chatbot_event_tdc/send_reminder.html'
    form_class = SendReminderForm

    def form_valid(self, form):
        event = form.cleaned_data['event']
        signup_query = Signup.objects.filter(event=event,
                                             reminded_datetime__isnull=True,
                                             fb_user__unsubscribe=False)
        fb_user_set = set(signup.fb_user for signup in signup_query)

        for fb_user in fb_user_set:
            text, button = utils.reminder_message_button(fb_user)
            status = post_button_message(event.fb_page,
                                         fb_user.fbid, text, button)
            if status == 'Success':
                for signup in fb_user.signup_set.filter(event=event):
                    signup.reminded_datetime = timezone.now()
                    signup.save()
                messages.success(
                    self.request,
                    ' '.join(('Reminder messages have been sent to ',
                              str(signup.fb_user.fbid), '.')))
            else:
                messages.error(
                    self.request,
                    ' '.join(('Reminder messages failed to be sent to ',
                              str(fb_user.fbid), '.')))
        return super(SendReminderView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(SendReminderView, self).get_context_data(**kwargs)
        context['fb_page'] = self.fb_page
        return context

    def get_form_kwargs(self):
        kwargs = super(SendReminderView, self).get_form_kwargs()
        kwargs['fb_page_id'] = self.kwargs['fb_page_id']
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy('fb_chatbot_event_tdc_send_reminder_status',
                            kwargs={'fb_page_id': self.fb_page.pk})

    @method_decorator(staff_member_required)
    @fb_page_required
    def dispatch(self, *args, **kwargs):
        return super(SendReminderView, self).dispatch(*args, **kwargs)


class SendReminderPreviewView(generic.View):

    def post(self, request, *args, **kwargs):
        id_event = request.POST.get('id_event')
        if id_event == '':
            return HttpResponseForbidden()
        event = Event.objects.get(pk=id_event)
        response_data = {}
        signup = Signup.objects.filter(event=event,
                                       fb_user__unsubscribe=False).first()
        message = utils.reminder_message_button(signup.fb_user)[0]
        response_data['message'] = message.replace(u'\n', u'<br>')
        return JsonResponse(response_data)

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(SendReminderPreviewView, self).dispatch(*args, **kwargs)


class SendReminderStatusView(generic.View):

    def get(self, request, *args, **kwargs):
        fb_page = self.fb_page
        return render(request,
                      'fb_chatbot_event_tdc/send_reminder_status.html',
                      {'fb_page': fb_page})

    @method_decorator(staff_member_required)
    @fb_page_required
    def dispatch(self, *args, **kwargs):
        return super(SendReminderStatusView, self).dispatch(*args, **kwargs)


def _redirect(view_name, query_dict):
    query_string = urllib.urlencode(query_dict)
    url = '%s?%s' % (reverse(view_name), query_string)
    return redirect(url)
