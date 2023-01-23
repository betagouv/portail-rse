from django import template

import impact.settings

register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def translate_boolean(boolean):
    return "oui" if boolean else "non"


@register.filter
def field_type(field):
    return field.field.__class__.__name__


@register.filter
def widget_type(field):
    if type(field) == str:
        return field
    return field.field.widget.__class__.__name__


@register.filter
def inline_static_file(path):
    full_path = impact.settings.STATICFILES_DIRS[0] / path
    with open(full_path) as f:
        content = f.read()
    return content
