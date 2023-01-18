from django import template
from django.utils.text import slugify

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
    return field.field.widget.__class__.__name__


@register.filter
def svelte_toggle_id(field):
    return f"svelte-toggle-{field.id_for_label}"

@register.filter
def svelte_container_id(field):
    return f"svelte-container-{field.id_for_label}"


@register.filter
def inline_static_file(path):
    full_path = impact.settings.STATICFILES_DIRS[0] / path
    with open(full_path) as f:
        content = f.read()
    return content
