from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def percentage(value):
    return mark_safe(format(value, '.3%'))


@register.filter
def format_nullable(value, replacement_field):
    if value is None:
        return 'N/A'
    else:
        return mark_safe(replacement_field.format(float(value)))
