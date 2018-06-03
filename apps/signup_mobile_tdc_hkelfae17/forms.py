# -*- coding: utf-8 -*-
import re

from django import forms

from signup_mobile_tdc_hkelfae17.models import Contact
from signup_mobile_tdc_hkelfae17.constants import (CHINESE,
                                                   ENGLISH,
                                                   REGION_CHOICES,
                                                   SIMPLIFIED_CHINESE)


class SignupForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'company', 'email',
                  'country_code', 'mobile_phone',
                  'country', 'eu_disclaimer']

    country = forms.CharField(widget=forms.HiddenInput(), initial='Unknown')
    country_code = forms.CharField(widget=forms.HiddenInput(), initial='ZZ')

    fb_psid = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, language=ENGLISH, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)

        if language == ENGLISH:
            self.fields['first_name'].error_messages = {
                'required': u'Required',
            }
            self.fields['last_name'].error_messages = {
                'required': u'Required',
            }
            self.fields['email'].error_messages = {
                'required': u'Email is required',
                'invalid': u'Enter a valid email',
            }
            self.fields['company'].error_messages = {
                'required': u'Company is required',
            }
            self.fields['mobile_phone'].error_messages = {
                'required': u'Phone is required',
                'invalid': u'Digits only',
            }

        elif language == CHINESE:
            self.fields['first_name'].error_messages = {
                'required': u'請填寫',
            }
            self.fields['last_name'].error_messages = {
                'required': u'請填寫',
            }
            self.fields['email'].error_messages = {
                'required': u'請填寫電郵',
                'invalid': u'請填寫正確電郵',
            }
            self.fields['company'].error_messages = {
                'required': u'請填寫公司名稱',
            }
            self.fields['mobile_phone'].error_messages = {
                'required': u'請填寫電話',
                'invalid': u'只限數字',
            }

        elif language == SIMPLIFIED_CHINESE:
            self.fields['first_name'].error_messages = {
                'required': u'请填写',
            }
            self.fields['last_name'].error_messages = {
                'required': u'请填写',
            }
            self.fields['email'].error_messages = {
                'required': u'请填写电邮',
                'invalid': u'请填写正确电邮',
            }
            self.fields['company'].error_messages = {
                'required': u'请填写公司名称',
            }
            self.fields['mobile_phone'].error_messages = {
                'required': u'请填写电话',
                'invalid': u'只限数字',
            }

    def clean_email(self):
        email = self.cleaned_data['email']
        if email.encode('utf-8') != email:
            msg = self.fields['email'].error_messages['required']
            raise forms.ValidationError(msg)

        return email

    def clean_mobile_phone(self):
        phone = self.cleaned_data['mobile_phone']
        if not phone:
            return phone

        phone_re = r'^[0-9]+$'
        error_msg = self.fields['mobile_phone'].error_messages['invalid']

        if not re.search(phone_re, phone):
            raise forms.ValidationError(error_msg)

        return phone


class WechatSignupForm(SignupForm):

    class Meta(SignupForm.Meta):
        model = Contact
        fields = SignupForm.Meta.fields + ['region']

    region = forms.ChoiceField(
        choices=(('', u'--- 请选择 ---'), ) + REGION_CHOICES,
        error_messages={'required': u'请选择'})
