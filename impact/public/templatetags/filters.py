from django import forms
from django import template
from django.conf import settings

import habilitations.models
import utils.anonymisation

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
    match field.field.widget:
        case forms.widgets.CheckboxInput() | forms.widgets.CheckboxSelectMultiple():
            return "fr-checkbox-group"
        case forms.widgets.Select():
            return "fr-select-group"
        case forms.widgets.RadioSelect():
            return "fr-radio-group"
        case forms.widgets.ClearableFileInput():
            return "fr-upload-group"
        case _:
            return "fr-input-group"


@register.filter
def get_field_display(field):
    if field.value() is None:
        return
    else:
        match field.field:
            case forms.ChoiceField():
                return dict(field.field.choices).get(field.value(), field.value())
            case _:
                return field.value()


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
    return habilitations.models.Habilitation.pour(entreprise, user)


@register.filter
def cache_partiellement_un_email(email):
    return utils.anonymisation.cache_partiellement_un_email(email)


@register.filter
def cache_partiellement_un_mot(mot):
    return utils.anonymisation.cache_partiellement_un_mot(mot)
