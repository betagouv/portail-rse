import pytest
from django.shortcuts import reverse
from django.utils.timezone import now

from reglementations.models import RapportCSRD

"""
Fragments HTMX pour la gestion de l'espace CSRD
"""


def _rapport_csrd_personnel(entreprise_non_qualifiee, alice, annee=now().year):
    entreprise_non_qualifiee.users.add(alice)
    rapport = RapportCSRD(
        entreprise=entreprise_non_qualifiee, proprietaire=alice, annee=annee
    )
    rapport.save()
    return rapport


@pytest.fixture
def rapport_csrd_courant(entreprise_non_qualifiee, alice):
    return _rapport_csrd_personnel(entreprise_non_qualifiee, alice)


@pytest.fixture
def rapport_csrd_precedent(entreprise_non_qualifiee, alice):
    return _rapport_csrd_personnel(
        entreprise_non_qualifiee, alice, annee=now().year - 1
    )


def test_soumission_lien_rapport(client, rapport_csrd_courant):
    # vérifie que la saisie du lien est bien effectuée
    url = reverse(
        "reglementations:soumettre_lien_rapport",
        kwargs={"csrd_id": rapport_csrd_courant.pk},
    )
    lien = "https://exemple.com/rapport_csrd"

    # avec un lien de rapport incorrect
    data = {"lien_rapport": "foo"}

    client.force_login(user=rapport_csrd_courant.proprietaire)
    response = client.post(url, data=data, follow=True)

    assert (
        400 == response.status_code
    ), "Cet URL n'est pas un lien de rapport CSRD valide"

    # avec un lien correct
    data |= {"lien_rapport": lien}
    response = client.post(url, data=data, follow=True)
    body = response.content.decode("utf-8")
    rapport_csrd_courant.refresh_from_db()

    assert response.status_code == 200
    assert (
        rapport_csrd_courant.lien_rapport == lien
    ), "Le lien du rapport n'est pas correctement enregistré"
    assert lien in body, "La réponse ne contient pas le lien du rapport"
    assert "Enregistré" in body, "Le lien n'est pas mentionné comme 'enregistré'"


def test_presence_annee_precedente(
    client, rapport_csrd_courant, rapport_csrd_precedent
):
    # vérifie si l'affichage du sélecteur contient bien les deux années (courant et précédente)
    url = reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": rapport_csrd_courant.entreprise.siren,
            "id_etape": "redaction-rapport-durabilite",
        },
    )
    client.force_login(user=rapport_csrd_courant.proprietaire)
    response = client.get(url)
    body = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f"_selection_{now().year}" in body
    assert f"_selection_{now().year-1}" in body


def test_selection_annee_rapport(client, rapport_csrd_courant, rapport_csrd_precedent):
    # verifie que la selection de l'annee est bien effectuée (session)
    url = reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": rapport_csrd_courant.entreprise.siren,
            "id_etape": "redaction-rapport-durabilite",
        },
    )
    client.force_login(user=rapport_csrd_courant.proprietaire)
    client.get(url)

    # aucun element de session enregistre pour le rapport CSRD : on utilise le rapport courant
    assert not client.session.get(
        "rapport_csrd_courant"
    ), "Aucune sélection de rapport CSRD (encore)"

    # sélection du rapport de l'année précédente (activation du fragment) :
    client.post(
        reverse(
            "reglementations:selection_rapport",
            kwargs={"csrd_id": rapport_csrd_precedent.pk},
        )
    )

    assert rapport_csrd_precedent.pk == client.session.get(
        "rapport_csrd_courant"
    ), "Le rapport CSRD actuel est différent du rapport sélectionné"
