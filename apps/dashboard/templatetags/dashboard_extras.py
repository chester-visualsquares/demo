from django import template
import pycountry

register = template.Library()


@register.filter
def country_name(value):
    try:
        alpha2 = value.upper()
        if alpha2 == 'TW':
            country_name = 'Taiwan'
        else:
            country_name = pycountry.countries.get(alpha2=alpha2).name
    except KeyError:
        country_name = value

    return country_name


@register.filter
def humanize_boolean(value):
    if value is True:
        return 'Yes'
    elif value is False:
        return 'No'
    else:
        return value


@register.filter
def humanize_list(value):
    if isinstance(value, type([])):
        return ' / '.join(value)
    else:
        return value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
