import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory

from entreprises.models import Entreprise
from habilitations.models import Habilitation
from oidc.views import _creation_entreprise
from oidc.views import _message_erreur_proprietaire
from oidc.views import dispatch_view


@pytest.mark.django_db
def test_creation_entreprise(alice, mocker):
    mock_api = mocker.patch("oidc.views.api_entreprise.infos_entreprise")
    mock_api.return_value = {
        "siren": "123456789",
        "denomination": "Test SARL",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "62.01Z",
    }

    entreprise = _creation_entreprise("123456789", alice)

    assert entreprise.siren == "123456789"
    assert entreprise.denomination == "Test SARL"
    assert entreprise.categorie_juridique_sirene == 5710
    assert entreprise.code_NAF == "62.01Z"

    # Vérifie que l'utilisateur est bien associé comme propriétaire
    assert Habilitation.existe(entreprise, alice)
    habilitation = Habilitation.objects.get(entreprise=entreprise, user=alice)
    assert habilitation.role == "proprietaire"


@pytest.mark.django_db
def test_creation_entreprise_appelle_api(alice, mocker):
    mock_api = mocker.patch("oidc.views.api_entreprise.infos_entreprise")
    mock_api.return_value = {
        "siren": "987654321",
        "denomination": "Entreprise Test",
        "categorie_juridique_sirene": 5499,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }

    _creation_entreprise("987654321", alice)

    mock_api.assert_called_once_with("987654321")


@pytest.mark.django_db
def test_message_erreur_proprietaire_un_seul(alice, entreprise_factory):
    entreprise = entreprise_factory(siren="111111111", utilisateur=alice)
    message = _message_erreur_proprietaire(entreprise)

    assert "Il existe déjà un propriétaire" in message
    assert str(entreprise) in message
    # Email doit être partiellement caché
    assert "a***e@" in message
    assert "contact@portail-rse.beta.gouv.fr" in message


@pytest.mark.django_db
def test_message_erreur_proprietaire_plusieurs(alice, bob, entreprise_factory):
    entreprise = entreprise_factory(siren="222222222")
    Habilitation.ajouter(entreprise, alice, role="proprietaire")
    Habilitation.ajouter(entreprise, bob, role="proprietaire")

    message = _message_erreur_proprietaire(entreprise)

    assert "Il existe déjà des propriétaires" in message
    assert str(entreprise) in message
    # Les deux emails doivent être présents (partiellement cachés)
    assert "a***e@" in message
    assert "b*b@" in message  # Bob a 3 caractères donc b*b@
    assert "contact@portail-rse.beta.gouv.fr" in message


@pytest.mark.django_db
def test_dispatch_view_sans_claims_leve_exception(alice):
    factory = RequestFactory()
    request = factory.get("/oidc/dispatch/")
    request.user = alice
    request.session = SessionStore()
    request.session.save()

    with pytest.raises(SuspiciousOperation, match="Impossible de trouver"):
        dispatch_view(request)


@pytest.mark.django_db
def test_dispatch_view_entreprise_inexistante_creation(alice, mocker, settings):
    settings.LOGIN_REDIRECT_URL = "/dashboard/"

    # Mock de l'API entreprise
    mock_api = mocker.patch("oidc.views.api_entreprise.infos_entreprise")
    mock_api.return_value = {
        "siren": "333333333",
        "denomination": "Nouvelle Entreprise",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "47.11F",
    }

    # Mock du logger
    mock_logger = mocker.patch("oidc.views.logger")

    factory = RequestFactory()
    request = factory.get("/oidc/dispatch/")
    request.user = alice
    request.session = SessionStore()
    request.session["oidc_user_claims"] = {
        "sub": "uuid-test-123",
        "siren": "333333333",
    }
    request.session.save()

    # Mock des messages Django
    from django.contrib.messages import get_messages
    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "_messages", FallbackStorage(request))

    response = dispatch_view(request)

    # Vérifie que l'entreprise a été créée
    entreprise = Entreprise.objects.get(siren="333333333")
    assert entreprise.denomination == "Nouvelle Entreprise"

    # Vérifie l'habilitation
    assert Habilitation.existe(entreprise, alice)

    # Vérifie la session
    assert request.session["entreprise"] == "333333333"

    # Vérifie la redirection
    assert response.status_code == 302
    assert response.url == "/dashboard/"

    # Vérifie les messages
    messages = list(get_messages(request))
    assert len(messages) == 1
    assert "a bien été créé" in str(messages[0])

    # Vérifie les logs
    mock_logger.info.assert_called()


@pytest.mark.django_db
def test_dispatch_view_entreprise_existante_utilisateur_membre(
    alice, entreprise_factory, mocker, settings
):
    settings.LOGIN_REDIRECT_URL = "/dashboard/"

    entreprise_factory(siren="444444444", utilisateur=alice)
    mocker.patch("oidc.views.logger")

    factory = RequestFactory()
    request = factory.get("/oidc/dispatch/")
    request.user = alice
    request.session = SessionStore()
    request.session["oidc_user_claims"] = {
        "sub": "uuid-alice-456",
        "siren": "444444444",
    }
    request.session.save()

    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "_messages", FallbackStorage(request))

    response = dispatch_view(request)

    # Vérifie la session
    assert request.session["entreprise"] == "444444444"

    # Vérifie la redirection
    assert response.status_code == 302
    assert response.url == "/dashboard/"

    # Vérifie les messages
    from django.contrib.messages import get_messages

    messages = list(get_messages(request))
    assert len(messages) == 1
    assert "ProConnect" in str(messages[0])


@pytest.mark.django_db
def test_dispatch_view_entreprise_existante_utilisateur_non_membre(
    alice, bob, entreprise_factory, mocker
):
    entreprise_factory(siren="555555555", utilisateur=bob)
    mocker.patch("oidc.views.logger")

    factory = RequestFactory()
    request = factory.get("/oidc/dispatch/")
    request.user = alice  # Alice n'est pas membre
    request.session = SessionStore()
    request.session["oidc_user_claims"] = {
        "sub": "uuid-alice-789",
        "siren": "555555555",
    }
    request.session.save()

    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "_messages", FallbackStorage(request))

    response = dispatch_view(request)

    # Vérifie que la session n'a pas été modifiée
    assert (
        "entreprise" not in request.session
        or request.session.get("entreprise") != "555555555"
    )

    # Vérifie la redirection vers la liste des entreprises
    assert response.status_code == 302
    assert "entreprises" in response.url

    # Vérifie le message d'avertissement
    from django.contrib.messages import get_messages

    messages = list(get_messages(request))
    assert len(messages) == 1
    assert "propriétaire" in str(messages[0]).lower()


@pytest.mark.django_db
def test_dispatch_view_entreprise_sans_proprietaire(alice, mocker, settings):
    settings.LOGIN_REDIRECT_URL = "/dashboard/"

    # Création d'une entreprise sans utilisateur
    entreprise = Entreprise.objects.create(
        siren="666666666",
        denomination="Entreprise Orpheline",
        categorie_juridique_sirene=5710,
        code_NAF="01.11Z",
    )

    mocker.patch("oidc.views.logger")

    factory = RequestFactory()
    request = factory.get("/oidc/dispatch/")
    request.user = alice
    request.session = SessionStore()
    request.session["oidc_user_claims"] = {
        "sub": "uuid-alice-000",
        "siren": "666666666",
    }
    request.session.save()

    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "_messages", FallbackStorage(request))

    response = dispatch_view(request)

    # Vérifie que l'utilisateur est devenu propriétaire
    assert Habilitation.existe(entreprise, alice)
    habilitation = Habilitation.objects.get(entreprise=entreprise, user=alice)
    assert habilitation.role == "proprietaire"

    # Vérifie la redirection
    assert response.status_code == 302
    assert response.url == "/dashboard/"


@pytest.mark.django_db
def test_dispatch_view_api_error(alice, mocker):
    from api.exceptions import APIError

    mock_api = mocker.patch("oidc.views.api_entreprise.infos_entreprise")
    mock_api.side_effect = APIError("Service indisponible")
    mock_logger = mocker.patch("oidc.views.logger")

    factory = RequestFactory()
    request = factory.get("/oidc/dispatch/")
    request.user = alice
    request.session = SessionStore()
    request.session["oidc_user_claims"] = {
        "sub": "uuid-alice-err",
        "siren": "777777777",
    }
    request.session.save()

    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "_messages", FallbackStorage(request))

    response = dispatch_view(request)

    # Vérifie que la réponse est une erreur 400
    assert response.status_code == 400
    assert "Impossible de contacter l'API entreprise" in response.content.decode()

    # Vérifie le log d'erreur
    mock_logger.error.assert_called()


@pytest.mark.django_db
def test_dispatch_view_exception_generique(alice, mocker):
    mock_api = mocker.patch("oidc.views.api_entreprise.infos_entreprise")
    mock_api.side_effect = Exception("Erreur inattendue")
    mock_logger = mocker.patch("oidc.views.logger")
    factory = RequestFactory()

    request = factory.get("/oidc/dispatch/")
    request.user = alice
    request.session = SessionStore()
    request.session["oidc_user_claims"] = {
        "sub": "uuid-alice-exc",
        "siren": "888888888",
    }
    request.session.save()

    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "_messages", FallbackStorage(request))

    response = dispatch_view(request)

    # Vérifie que la réponse est une erreur 500
    assert response.status_code == 500
    assert "888888888" in response.content.decode()

    # Vérifie le log d'erreur
    mock_logger.error.assert_called()
