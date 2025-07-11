from django import template

register = template.Library()

@register.filter(name='snake_to_readable')
def snake_to_readable(value):
    components = value.split('_')
    return ' '.join(x.capitalize() for x in components)