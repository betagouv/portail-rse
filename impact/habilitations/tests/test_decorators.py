from unittest.mock import Mock

import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from habilitations.decorators import role
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from users.models import User


# Exemple de vue pour les tests
def example_view(_):
    return HttpResponse("OK")


@pytest.fixture
def mock_request(entreprise_non_qualifiee, alice):
    request = Mock()
    request.user = alice
    request.session = {"entreprise": entreprise_non_qualifiee.siren}
    request.entreprises = [entreprise_non_qualifiee]
    Habilitation(user=alice, entreprise=entreprise_non_qualifiee).save()
    return request


# Test pour un utilisateur avec le rôle PROPRIETAIRE
def test_role_proprietaire(mock_request):
    mock_request.user.role = UserRole.PROPRIETAIRE
    decorated_view = role(UserRole.PROPRIETAIRE)(example_view)
    response = decorated_view(mock_request)
    print(response.content)
    assert response.status_code == 200
    assert response.content == b"OK"


# Test pour un utilisateur avec le rôle EDITEUR
def test_role_editeur(mock_request):
    mock_request.user.role = UserRole.EDITEUR
    decorated_view = role(UserRole.EDITEUR)(example_view)
    response = decorated_view(mock_request)
    assert response.status_code == 200
    assert response.content == b"OK"


# Test pour un utilisateur avec le rôle LECTEUR
def test_role_lecteur(mock_request):
    mock_request.user.role = UserRole.LECTEUR
    decorated_view = role(UserRole.LECTEUR)(example_view)
    response = decorated_view(mock_request)
    assert response.status_code == 200
    assert response.content == b"OK"


# Test pour un utilisateur sans les droits nécessaires
def test_role_forbidden(alice, entreprise_non_qualifiee):
    # Utiliser Habilitation.ajouter() pour créer correctement la relation
    Habilitation.ajouter(entreprise_non_qualifiee, alice, UserRole.LECTEUR)

    # Recharger alice pour avoir les relations à jour
    alice = User.objects.prefetch_related("entreprise_set", "habilitation_set").get(
        pk=alice.pk
    )

    mock_request = Mock()
    mock_request.user = alice
    mock_request.session = {"entreprise": entreprise_non_qualifiee.siren}

    decorated_view = role(UserRole.PROPRIETAIRE)(example_view)

    with pytest.raises(PermissionDenied, match="L'utilisateur n'a pas le rôle requis"):
        decorated_view(mock_request)


# Test pour un utilisateur avec un rôle supérieur
def test_role_superieur(mock_request):
    mock_request.user.role = UserRole.PROPRIETAIRE
    decorated_view = role(UserRole.EDITEUR)(example_view)
    response = decorated_view(mock_request)
    assert response.status_code == 200
    assert response.content == b"OK"
