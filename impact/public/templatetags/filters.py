from django import template
from django.conf import settings
from django.forms import BooleanField
from django.forms import ChoiceField
from django.forms import FileField

import habilitations.models

register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def translate_boolean(boolean):
    return "oui" if boolean else "non"


@register.filter
def display_field(field):
    if field in (None, ""):
        return "non renseigné"
    elif isinstance(field, bool):
        return "oui" if field else "non"
    else:
        return field
    return field if field else "non renseigné"


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
def fr_group_class(field):
    if isinstance(field.field, BooleanField):
        return "fr-checkbox-group"
    elif isinstance(field.field, ChoiceField):
        return "fr-select-group"
    elif isinstance(field.field, FileField):
        return "fr-upload-group"
    else:
        return "fr-input-group"


@register.filter
def inline_static_file(path):
    full_path = settings.STATICFILES_DIRS[0] / path
    with open(full_path) as f:
        content = f.read()
    return content


@register.filter
def model_field(instance, field_name):
    return instance.__class__._meta.get_field(field_name)


@register.filter
def field_value(instance, field_name):
    return getattr(instance, field_name)


@register.filter
def model_field_type(model_field):
    return model_field.__class__.__name__


@register.filter
def habilitation(user, entreprise):
    return habilitations.models.get_habilitation(user, entreprise)
