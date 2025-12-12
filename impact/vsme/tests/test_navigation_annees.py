from datetime import date

import pytest
from django.urls import reverse

from vsme.models import get_annee_max_valide
from vsme.models import get_annee_rapport_par_defaut
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
    annee_par_defaut = get_annee_rapport_par_defaut(entreprise)
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
    if annee <= get_annee_max_valide(entreprise):
        url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee])
        response = client.get(url)

        assert response.status_code == 200
        assert RapportVSME.objects.filter(entreprise=entreprise, annee=annee).exists()


def test_acces_annee_n_plus_1_avec_cloture_30_juin(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()
    client.force_login(alice)

    annee_n_plus_1 = date.today().year + 1
    url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee_n_plus_1])
    response = client.get(url)

    assert response.status_code == 200
    assert RapportVSME.objects.filter(
        entreprise=entreprise, annee=annee_n_plus_1
    ).exists()


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

    # Pour une clôture 31/12, l'année max est N, donc N+1 est invalide
    annee_invalide = get_annee_max_valide(entreprise) + 1
    url = reverse("vsme:categories_vsme", args=[entreprise.siren, annee_invalide])
    response = client.get(url)

    assert response.status_code == 302  # Redirection


def test_contexte_contient_annees_disponibles_cloture_31_decembre(
    client, entreprise_factory, alice
):
    """Avec clôture 31/12, les années disponibles vont de 2020 à N"""
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 12, 31)
    entreprise.save()
    client.force_login(alice)

    url = reverse("vsme:categories_vsme", args=[entreprise.siren])
    response = client.get(url)

    assert "annees_disponibles" in response.context
    assert "annee_courante" in response.context
    assert "annee_par_defaut" in response.context

    annees = response.context["annees_disponibles"]
    assert 2020 in annees
    assert get_annee_rapport_par_defaut(entreprise) in annees
    assert date.today().year in annees  # N est disponible
    assert date.today().year + 1 not in annees  # N+1 n'est pas disponible


def test_contexte_contient_annees_disponibles_cloture_30_juin(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    entreprise.date_cloture_exercice = date(2023, 6, 30)
    entreprise.save()
    client.force_login(alice)

    url = reverse("vsme:categories_vsme", args=[entreprise.siren])
    response = client.get(url)

    annees = response.context["annees_disponibles"]
    assert 2020 in annees
    assert date.today().year in annees
    assert date.today().year + 1 in annees  # N+1 est disponible


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
