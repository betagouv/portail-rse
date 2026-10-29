from string.templatelib import convert
from string.templatelib import Interpolation
from string.templatelib import Template

from django.contrib import messages
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

# Les fonctions *_sans_html affichent le message tel quel : tout HTML est échappé par le template.
# Les fonctions *_avec_html prennent une t-string (t"...") : le HTML écrit dans la t-string
# est conservé, les valeurs insérées sont échappées.


def _html(message):
    if not isinstance(message, Template):
        raise TypeError('Le message doit être une t-string : t"..."')
    morceaux = []
    for morceau in message:
        if isinstance(morceau, Interpolation):
            valeur = convert(morceau.value, morceau.conversion)
            morceaux.append(conditional_escape(format(valeur, morceau.format_spec)))
        else:
            morceaux.append(morceau)
    return mark_safe("".join(morceaux))


def message_success_sans_html(request, message):
    messages.success(request, message)


def message_success_avec_html(request, message):
    messages.success(request, _html(message))


def message_info_sans_html(request, message):
    messages.info(request, message)


def message_info_avec_html(request, message):
    messages.info(request, _html(message))


def message_warning_sans_html(request, message):
    messages.warning(request, message)


def message_warning_avec_html(request, message):
    messages.warning(request, _html(message))


def message_error_sans_html(request, message):
    messages.error(request, message)


def message_error_avec_html(request, message):
    messages.error(request, _html(message))
