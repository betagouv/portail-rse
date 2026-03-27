from django.urls.base import reverse

from conftest import CODE_SA
from vsme.models import RapportVSME
from vsme.tests.test_indicateurs import INDICATEURS_VSME_BASE_URL
from vsme.views import preremplit_indicateur


def test_preremplit_indicateur_qu_on_ne_sait_pas_preremplir(rapport_vsme):
    indicateur_schema_id = "B1-24-a"  # indicateur choix module

    preremplissage = preremplit_indicateur(indicateur_schema_id, rapport_vsme)

    assert preremplissage == {}


def test_preremplit_indicateur_forme_juridique(rapport_vsme):
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    indicateur_schema_id = "B1-24-e-i"

    preremplissage = preremplit_indicateur(indicateur_schema_id, rapport_vsme)

    assert preremplissage == {
        "initial": {
            "forme_juridique": "55",
            "coopérative": False,
        },
        "source": {
            "nom": "l'Annuaire des Entreprise",
            "url": "https://annuaire-entreprises.data.gouv.fr/",
        },
    }


def test_preremplit_indicateur_forme_juridique_entreprise_sans_categorie_juridique_sirene(
    rapport_vsme,
):
    # Cas marginal mais il pourrait y avoir des entreprises sans catégorie juridique sirene en base
    # si celle-ci n'a pas (ou mal) été récupérée par API à la création de l'entreprise
    rapport_vsme.entreprise.categorie_juridique_sirene = None
    indicateur_schema_id = "B1-24-e-i"

    preremplissage = preremplit_indicateur(indicateur_schema_id, rapport_vsme)

    assert preremplissage == {}


def test_indicateur_prerempli_affiche_le_preremplissage(client, alice, rapport_vsme):
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL + f"{rapport_vsme.id}/indicateur/B1-24-e-i/"
    response = client.get(url)

    assert response.status_code == 200
    context = response.context
    content = response.content.decode("utf-8")
    assert "Annuaire des Entreprise" in content, content
    assert context["multiform"].forms[0]["forme_juridique"].value() == "55"


def test_indicateur_deja_complete_n_affiche_pas_le_preremplissage(
    client, alice, rapport_vsme
):
    indicateur_forme_juridique = "B1-24-e-i"
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    rapport_vsme.indicateurs.create(
        schema_id=indicateur_forme_juridique,
        data={"forme_juridique": "11"},
    )
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL + f"{rapport_vsme.id}/indicateur/B1-24-e-i/"
    response = client.get(url)

    assert response.status_code == 200
    context = response.context
    content = response.content.decode("utf-8")
    assert "Annuaire des Entreprise" not in content
    assert context["multiform"].forms[0]["forme_juridique"].value() == "11"


def test_preremplit_indicateur_taux_rotation_personnel_nb_salaries_inferieur_a_50(
    rapport_vsme,
):
    indicateur_nombre_salaries = "B1-24-e-v"
    rapport_vsme.indicateurs.create(
        schema_id=indicateur_nombre_salaries, data={"nombre_salaries": 49}
    )

    indicateur_taux_rotation_personnel = "B8-40"
    preremplissage = preremplit_indicateur(
        indicateur_taux_rotation_personnel, rapport_vsme
    )

    assert preremplissage == {
        "initial": {"non_pertinent": True},
        "source": {
            "nom": "l'indicateur Nombre de salariés dans B1",
            "url": reverse(
                "vsme:exigence_de_publication_vsme",
                args=[rapport_vsme.id, "B1"],
            ),
        },
    }


def test_preremplit_indicateur_taux_rotation_personnel_nb_salaries_superieur_a_50(
    rapport_vsme,
):
    indicateur_nombre_salaries = "B1-24-e-v"
    rapport_vsme.indicateurs.create(
        schema_id=indicateur_nombre_salaries, data={"nombre_salaries": 50}
    )

    indicateur_taux_rotation_personnel = "B8-40"
    preremplissage = preremplit_indicateur(
        indicateur_taux_rotation_personnel, rapport_vsme
    )

    assert preremplissage == {}


def test_preremplit_indicateur_taux_rotation_personnel_nb_salaries_non_renseigne(
    rapport_vsme,
):
    indicateur_taux_rotation_personnel = "B8-40"
    preremplissage = preremplit_indicateur(
        indicateur_taux_rotation_personnel, rapport_vsme
    )

    assert preremplissage == {}


def test_preremplit_indicateur_ecart_remuneration_hommes_femmes_nb_salaries_inferieur_a_150(
    rapport_vsme,
):
    indicateur_nombre_salaries = "B1-24-e-v"
    rapport_vsme.indicateurs.create(
        schema_id=indicateur_nombre_salaries, data={"nombre_salaries": 149}
    )

    indicateur_ecart_remuneration_hommes_femmes = "B10-42-b"
    preremplissage = preremplit_indicateur(
        indicateur_ecart_remuneration_hommes_femmes, rapport_vsme
    )

    assert preremplissage == {
        "initial": {"non_pertinent": True},
        "source": {
            "nom": "l'indicateur Nombre de salariés dans B1",
            "url": reverse(
                "vsme:exigence_de_publication_vsme",
                args=[rapport_vsme.id, "B1"],
            ),
        },
    }


def test_preremplit_indicateur_ecart_remuneration_hommes_femmes_nb_salaries_superieur_a_150(
    rapport_vsme,
):
    indicateur_nombre_salaries = "B1-24-e-v"
    rapport_vsme.indicateurs.create(
        schema_id=indicateur_nombre_salaries, data={"nombre_salaries": 150}
    )

    indicateur_ecart_remuneration_hommes_femmes = "B10-42-b"
    preremplissage = preremplit_indicateur(
        indicateur_ecart_remuneration_hommes_femmes, rapport_vsme
    )

    assert preremplissage == {}


def test_preremplit_indicateur_ecart_remuneration_hommes_femmes_nb_salaries_non_renseigne(
    rapport_vsme,
):
    indicateur_ecart_remuneration_hommes_femmes = "B10-42-b"
    preremplissage = preremplit_indicateur(
        indicateur_ecart_remuneration_hommes_femmes, rapport_vsme
    )

    assert preremplissage == {}


def test_preremplit_un_indicateur_si_déjà_rempli_une_année_précédente(
    rapport_vsme,
):
    entreprise = rapport_vsme.entreprise
    un_an_avant = rapport_vsme.annee - 1
    deux_ans_avant = rapport_vsme.annee - 2
    trois_ans_avant = rapport_vsme.annee - 3
    # instancier rapport_vsme_trois_ans_avant avant rapport_vsme_deux_ans_avant
    # permet de contraindre le tri par année
    rapport_vsme_trois_ans_avant = RapportVSME.objects.create(
        entreprise=entreprise, annee=trois_ans_avant
    )
    rapport_vsme_deux_ans_avant = RapportVSME.objects.create(
        entreprise=entreprise, annee=deux_ans_avant
    )
    rapport_vsme_un_an_avant = RapportVSME.objects.create(
        entreprise=entreprise, annee=un_an_avant
    )
    schema_id = "B2-26-p1"
    rapport_vsme_deux_ans_avant.indicateurs.create(
        schema_id=schema_id,
        data={"participation_gouvernance": "explications à réutiliser"},
    )
    rapport_vsme_trois_ans_avant.indicateurs.create(
        schema_id=schema_id,
        data={"participation_gouvernance": "explications trop vieille"},
    )

    preremplissage = preremplit_indicateur(schema_id, rapport_vsme)

    assert preremplissage == {
        "initial": {"participation_gouvernance": "explications à réutiliser"},
        "source": {
            "nom": f"votre rapport VSME {deux_ans_avant}",
            "url": reverse(
                "vsme:exigence_de_publication_vsme",
                args=[rapport_vsme_deux_ans_avant.id, "B2"],
            ),
        },
    }


def test_ne_preremplit_pas_un_indicateur_si_déjà_rempli_dans_le_futur(
    rapport_vsme,
):
    entreprise = rapport_vsme.entreprise
    un_an_apres = rapport_vsme.annee + 1
    rapport_vsme_un_an_apres = RapportVSME.objects.create(
        entreprise=entreprise, annee=un_an_apres
    )
    schema_id = "B2-26-p1"
    rapport_vsme_un_an_apres.indicateurs.create(
        schema_id=schema_id, data={"participation_gouvernance": "explications"}
    )

    preremplissage = preremplit_indicateur(schema_id, rapport_vsme)

    assert preremplissage == {}
