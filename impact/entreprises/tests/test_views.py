import pytest
from django.urls import reverse

from entreprises.models import Entreprise, Habilitation
from users.forms import UserCreationForm
from users.models import User


def test_entreprises_page_requires_login(client):
    response = client.get("/entreprises")

    assert response.status_code == 302


def test_entreprises_page_for_logged_user(client, django_user_model):
    entreprise = Entreprise.objects.create(siren="123456789")
    user = django_user_model.objects.create()
    entreprise.users.add(user)
    client.force_login(user)

    response = client.get("/entreprises")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page entreprises -->" in content