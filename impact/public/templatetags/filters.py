from django import template

register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def translate_boolean(boolean):
    return "oui" if boolean else "non"


@register.filter
def widget_type(field):
    return field.field.widget.__class__.__name__
