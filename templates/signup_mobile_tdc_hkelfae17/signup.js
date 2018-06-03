/*global jQuery: false*/
(function($) {
  'use strict';

  $(document).ready(function() {
    var $first_name_field = $('#id_first_name'),
        $last_name_field = $('#id_last_name'),
        $email_field = $('#id_email'),
        $company_field = $('#id_company'),
        $mobile_phone_field = $('#id_mobile_phone'),        
        first_name_err_msg = '{{ form.first_name.errors|first|default:"None" }}',
        last_name_err_msg = '{{ form.last_name.errors|first|default:"None" }}',
        email_err_msg = '{{ form.email.errors|first|default:"None" }}',
        company_err_msg = '{{ form.company.errors|first|default:"None" }}',
        mobile_phone_err_msg = '{{ form.mobile_phone.errors|first|default:"None" }}';

    if (first_name_err_msg !== 'None') {
      $first_name_field.addClass('error')
                  .removeClass('input_default_text')
                  .val(first_name_err_msg);

      $first_name_field.filter('.error').focus(function() {
        $first_name_field.removeClass('error')
                    .val('');
      });
    }

    if (last_name_err_msg !== 'None') {
      $last_name_field.addClass('error')
                  .removeClass('input_default_text')
                  .val(last_name_err_msg);

      $last_name_field.filter('.error').focus(function() {
        $last_name_field.removeClass('error')
                    .val('');
      });
    }

    if (email_err_msg !== 'None') {
      $email_field.addClass('error')
                  .removeClass('input_default_text')
                  .val(email_err_msg);

      $email_field.filter('.error').focus(function() {
        $email_field.removeClass('error')
                    .val('');
      });
    }

    if (company_err_msg !== 'None') {
      $company_field.addClass('error')
                  .removeClass('input_default_text')
                  .val(company_err_msg);

      $company_field.filter('.error').focus(function() {
        $company_field.removeClass('error')
                    .val('');
      });
    }

    if (mobile_phone_err_msg !== 'None') {
      $mobile_phone_field.addClass('error')
                  .removeClass('input_default_text')
                  .val(mobile_phone_err_msg);

      $mobile_phone_field.filter('.error').focus(function() {
        $mobile_phone_field.removeClass('error')
                    .val('');
      });
    }

    // Prevent submitting error messages
    $('#contact').submit(function() {
      if ($first_name_field.val() === first_name_err_msg) {
        $first_name_field.val('');
      }

      if ($last_name_field.val() === last_name_err_msg) {
        $last_name_field.val('');
      }

      if ($email_field.val() === email_err_msg) {
        $email_field.val('');
      }

      if ($company_field.val() === company_err_msg) {
        $company_field.val('');
      }

      if ($mobile_phone_field.val() === mobile_phone_err_msg) {
        $mobile_phone_field.val('');
      }
    });
  });
}(jQuery));
