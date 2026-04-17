from datetime import date

import pytest
from django.urls import reverse
from freezegun import freeze_time

from vsme.models import RapportVSME


def test_acces_sans_annee_utilise_annee_par_defaut(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    # Entreprise avec clôture au 31/12, donc année par défaut = N-1
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    url = reverse("vsme:categories_vsme", args=[entreprise.siren])
    response = client.get(url)

    assert response.status_code == 200
    annee_par_defaut = entreprise.dernier_exercice_clos.date_cloture.year
    assert RapportVSME.objects.filter(
        entreprise=entreprise, annee=annee_par_defaut
    ).exists()


@pytest.mark.parametrize("annee", [2020, 2021, 2022, 2023, 2024])
def test_acces_avec_annee_valide(client, entreprise_factory, alice, annee):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    # Vérifier que l'année est valide pour cette entreprise
    url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee])
    response = client.get(url)

    assert response.status_code == 200
    assert RapportVSME.objects.filter(entreprise=entreprise, annee=annee).exists()


@freeze_time("2025-12-12")
def test_acces_annee_n_plus_1_avec_cloture_30_juin(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()
    client.force_login(alice)

    annee_n_plus_1 = 2026  # N+1 pour 2025
    url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee_n_plus_1])
    response = client.get(url)

    assert response.status_code == 200
    assert RapportVSME.objects.filter(
        entreprise=entreprise, annee=annee_n_plus_1
    ).exists()


def test_acces_avec_annee_valide_en_paramètre(client, entreprise_factory, alice):
    """utile pour le changement d'année en HTMX"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    url = reverse("vsme:categories_vsme", args=[entreprise.siren]) + "?annee=2026"
    response = client.get(url, headers={"HX-Request": "true"}, follow=False)

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == reverse(
        "vsme:categories_vsme", args=[entreprise.siren, 2026]
    )


@pytest.mark.parametrize(
    "annee",
    [
        2019,  # Avant 2020
        2018,
    ],
)
def test_acces_avec_annee_invalide(client, entreprise_factory, alice, annee):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee])
    response = client.get(url)

    assert response.status_code == 302  # Redirection
    assert not RapportVSME.objects.filter(entreprise=entreprise, annee=annee).exists()


def test_acces_annee_future_invalide(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    annee_invalide = entreprise.dernier_exercice_clos.suivant().date_cloture.year + 1
    url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee_invalide])
    response = client.get(url)

    assert response.status_code == 302  # Redirection


def test_message_info_annee_non_defaut(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    # Créer un rapport pour 2022 (année non par défaut)
    url = reverse("vsme:categories_vsme", args=[entreprise.siren, 2022])
    response = client.get(url, follow=True)

    # Vérifier qu'un message d'info est présent
    messages = list(response.context["messages"])
    assert len(messages) > 0
    assert any("2022" in str(message) for message in messages)


def test_navigation_entre_annees(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    # Créer un rapport 2024
    url_2024 = reverse("vsme:categories_vsme", args=[entreprise.siren, 2024])
    response_2024 = client.get(url_2024)
    assert response_2024.status_code == 200
    rapport_2024 = response_2024.context["rapport_vsme"]
    assert rapport_2024.annee == 2024

    # Créer un rapport 2023
    url_2023 = reverse("vsme:categories_vsme", args=[entreprise.siren, 2023])
    response_2023 = client.get(url_2023)
    assert response_2023.status_code == 200
    rapport_2023 = response_2023.context["rapport_vsme"]
    assert rapport_2023.annee == 2023

    # Vérifier que ce sont deux rapports distincts
    assert rapport_2024.id != rapport_2023.id
    assert entreprise.rapports_vsme.count() == 2


def test_get_or_create_ne_duplique_pas(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    url = reverse("vsme:categories_vsme", args=[entreprise.siren, 2023])

    # Premier accès
    client.get(url)
    count_1 = RapportVSME.objects.filter(entreprise=entreprise, annee=2023).count()

    # Deuxième accès
    client.get(url)
    count_2 = RapportVSME.objects.filter(entreprise=entreprise, annee=2023).count()

    assert count_1 == 1
    assert count_2 == 1
