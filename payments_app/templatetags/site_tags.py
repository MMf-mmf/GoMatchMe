from django import template
from datetime import datetime, date

register = template.Library()

@register.filter
def str_to_bool(value):
    if value == '' or value is None:
        return 'false'
    else:
        if isinstance(value, bool):
            return str(value).lower()
        return value.lower()