import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template import Context
from django.template import Template
from django.test import RequestFactory

from utils.messages import message_error_avec_html
from utils.messages import message_error_sans_html
from utils.messages import message_info_avec_html
from utils.messages import message_info_sans_html
from utils.messages import message_success_avec_html
from utils.messages import message_success_sans_html
from utils.messages import message_warning_avec_html
from utils.messages import message_warning_sans_html


@pytest.fixture
def request_avec_messages():
    request = RequestFactory().get("/")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.parametrize(
    "fonction, niveau",
    [
        (message_success_sans_html, "success"),
        (message_info_sans_html, "info"),
        (message_warning_sans_html, "warning"),
        (message_error_sans_html, "error"),
    ],
)
def test_sans_html_sera_echappe_par_le_template(
    request_avec_messages, fonction, niveau
):
    fonction(request_avec_messages, "<b>Alice</b> & Bob")

    [message] = get_messages(request_avec_messages)
    assert message.level_tag == niveau
    assert Template("{{ message }}").render(Context({"message": message})) == (
        "&lt;b&gt;Alice&lt;/b&gt; &amp; Bob"
    )


@pytest.mark.parametrize(
    "fonction, niveau",
    [
        (message_success_avec_html, "success"),
        (message_info_avec_html, "info"),
        (message_warning_avec_html, "warning"),
        (message_error_avec_html, "error"),
    ],
)
def test_avec_html_conserve_le_html_et_echappe_les_valeurs(
    request_avec_messages, fonction, niveau
):
    url = "/profil"
    nom = "<b>Alice</b>"

    fonction(request_avec_messages, t"<a href='{url}'>{nom}</a>")

    [message] = get_messages(request_avec_messages)
    assert message.level_tag == niveau
    assert Template("{{ message }}").render(Context({"message": message})) == (
        "<a href='/profil'>&lt;b&gt;Alice&lt;/b&gt;</a>"
    )


def test_avec_html_applique_conversion_et_format(request_avec_messages):
    nom = "<b>"
    montant = 3.14159

    message_success_avec_html(request_avec_messages, t"{nom!r} {montant:.2f}")

    [message] = get_messages(request_avec_messages)
    assert message.message == "&#x27;&lt;b&gt;&#x27; 3.14"


@pytest.mark.parametrize(
    "fonction",
    [
        message_success_avec_html,
        message_info_avec_html,
        message_warning_avec_html,
        message_error_avec_html,
    ],
)
def test_avec_html_refuse_une_chaine_qui_n_est_pas_une_t_string(
    request_avec_messages, fonction
):
    nom = "<b>Alice</b>"

    with pytest.raises(TypeError):
        fonction(request_avec_messages, f"<a href='/profil'>{nom}</a>")

    assert list(get_messages(request_avec_messages)) == []
