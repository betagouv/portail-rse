import pytest
from django.test import RequestFactory

from oidc.context_processors import proconnect


@pytest.fixture
def oidc_disabled(settings):
    settings.OIDC_ENABLED = False


@pytest.mark.django_db
def test_proconnect_true_avec_oidc_id_token():
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {"oidc_id_token": "fake-token-12345"}

    context = proconnect(request)

    assert context["proconnect"] is True
    assert context["oidc_enabled"] is True


@pytest.mark.django_db
def test_proconnect_false_sans_oidc_id_token():
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {}

    context = proconnect(request)

    assert context["proconnect"] is False
    assert context["oidc_enabled"] is True


@pytest.mark.django_db
def test_oidc_enabled_false(oidc_disabled):
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {"oidc_id_token": "fake-token"}

    context = proconnect(request)

    assert context["proconnect"] is True  # Token présent
    assert context["oidc_enabled"] is False  # Mais OIDC désactivé


@pytest.mark.django_db
def test_context_processor_retourne_dictionnaire():
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {}

    context = proconnect(request)

    assert isinstance(context, dict)
    assert "proconnect" in context
    assert "oidc_enabled" in context
    assert len(context) == 2
