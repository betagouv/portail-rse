import json
from datetime import date

import pytest
from requests.exceptions import Timeout

from api.exceptions import APIError
from api.ratios_financiers import dernier_exercice_comptable
from api.ratios_financiers import RATIOS_FINANCIERS_TIMEOUT
from api.tests import MockedResponse
from entreprises.models import CaracteristiquesAnnuelles


SIREN = "123456789"


@pytest.mark.network
def test_api_fonctionnelle():
    siren = 552032534  # DANONE

    data = dernier_exercice_comptable(siren)

    assert len(data) == 3
    assert type(data["date_cloture_exercice"]) == date
    assert data["tranche_chiffre_affaires"] in [
        ca for ca, label in CaracteristiquesAnnuelles.CA_CHOICES
    ]
    assert data["tranche_chiffre_affaires_consolide"] in [
        ca for ca, label in CaracteristiquesAnnuelles.CA_CONSOLIDE_CHOICES
    ]


def test_pas_de_resultat(mocker):
    # Réponse type de l'API sans résultat trouvé
    content = """{"nhits": 0, "parameters": {"dataset": "ratios_inpi_bce", "q": "siren = 889297453", "rows": 10, "start": 0, "sort": ["date_cloture_exercice"], "format": "json", "timezone": "UTC"}, "records": []}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(content))
    )

    data = dernier_exercice_comptable(SIREN)

    faked_request.assert_called_once_with(
        "https://data.economie.gouv.fr/api/records/1.0/search/",
        params={
            "dataset": "ratios_inpi_bce",
            "q": f"siren={SIREN}",
            "sort": "date_cloture_exercice",
        },
        timeout=RATIOS_FINANCIERS_TIMEOUT,
    )
    assert data == {
        "date_cloture_exercice": None,
        "tranche_chiffre_affaires": None,
        "tranche_chiffre_affaires_consolide": None,
    }


def test_pas_de_bilan_consolide(mocker):
    # Réponse type tronquée de l'API avec 2 derniers bilans complets et pas de bilan consolidé 511278533 3MEDIA
    content = """{"nhits": 6, "parameters": {"dataset": "ratios_inpi_bce", "q": "siren = 511278533", "rows": 10, "start": 0, "sort": ["date_cloture_exercice"], "format": "json", "timezone": "UTC"}, "records": [{"datasetid": "ratios_inpi_bce", "recordid": "55580925dd686878088d827f4712e2f3aef7cd83", "fields": {"marge_brute": 15711568, "poids_bfr_exploitation_sur_ca": 5.575, "caf_sur_ca": -9.299, "ratio_de_vetuste": 14.647, "autonomie_financiere": -21.002, "date_cloture_exercice": "2021-12-31", "marge_ebe": -9.153, "ratio_de_liquidite": 82.502, "ebe": -1438048, "resultat_net": -1147009, "taux_d_endettement": -0.552, "confidentiality": "Public", "poids_bfr_exploitation_sur_ca_jours": 20.07, "credit_clients_jours": 42.966, "chiffre_d_affaires": 15711568, "resultat_courant_avant_impots_sur_ca": -7.309, "ebit": -1159715, "type_bilan": "C", "couverture_des_interets": -0.042, "credit_fournisseurs_jours": 99.673, "rotation_des_stocks_jours": 0.0, "siren": "511278533", "capacite_de_remboursement": 0.0}, "record_timestamp": "2024-03-18T22:16:13.633Z"}, {"datasetid": "ratios_inpi_bce", "recordid": "189d6361b965075979ea4af728292e87288be8a3", "fields": {"marge_brute": 17188502, "poids_bfr_exploitation_sur_ca": 14.671, "caf_sur_ca": 5.198, "ratio_de_vetuste": 17.642, "autonomie_financiere": 30.723, "date_cloture_exercice": "2020-12-31", "marge_ebe": 9.014, "ratio_de_liquidite": 148.939, "ebe": 1549389, "resultat_net": 760061, "taux_d_endettement": 0.395, "confidentiality": "Public", "poids_bfr_exploitation_sur_ca_jours": 52.815, "credit_clients_jours": 16.649, "chiffre_d_affaires": 1718850200, "resultat_courant_avant_impots_sur_ca": 8.069, "ebit": 1390231, "type_bilan": "C", "couverture_des_interets": 0.495, "credit_fournisseurs_jours": 60.076, "rotation_des_stocks_jours": 0.0, "siren": "511278533", "capacite_de_remboursement": 0.008}, "record_timestamp": "2024-03-18T22:16:13.633Z"}]}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(content))
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": date(2021, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_chiffre_affaires_consolide": None,
    }


def test_bilan_complet_et_bilan_consolide(mocker):
    # Réponse type tronquée de l'API avec 1 dernier bilan complet et 1 dernier bilan consolidé 552032534 DANONE
    content = """{"nhits":13,"parameters":{"dataset":"ratios_inpi_bce","q":"siren = 552032534","rows":10,"start":0,"sort":["date_cloture_exercice"],"format":"json","timezone":"UTC"},"records":[{"datasetid":"ratios_inpi_bce","recordid":"a911bf2fce0b993b8827a7bbc4d3114c0ed8021c","fields":{"marge_brute":11521000000,"poids_bfr_exploitation_sur_ca":46.938,"caf_sur_ca":5.791,"autonomie_financiere":179.52,"date_cloture_exercice":"2022-12-31","marge_ebe":13.756,"ratio_de_liquidite":0,"ebe":3340000000,"resultat_net":0,"taux_d_endettement":20.366,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":168.977,"credit_clients_jours":0,"chiffre_d_affaires":24281000000,"resultat_courant_avant_impots_sur_ca":8.216,"ebit":2257000000,"type_bilan":"K","couverture_des_interets":18.443,"credit_fournisseurs_jours":57.275,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":11.796},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"714b8ab05369c061f2ac2ac719a6f17832a4761f","fields":{"marge_brute":635000000,"poids_bfr_exploitation_sur_ca":-195.433,"caf_sur_ca":602.205,"ratio_de_vetuste":38.298,"autonomie_financiere":47.213,"date_cloture_exercice":"2022-12-31","marge_ebe":60,"ratio_de_liquidite":21.361,"ebe":381000000,"resultat_net":3674000000,"taux_d_endettement":92.375,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-703.559,"credit_clients_jours":0,"chiffre_d_affaires":635000000,"resultat_courant_avant_impots_sur_ca":609.606,"ebit":-137000000,"type_bilan":"C","couverture_des_interets":60.892,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":3.865},"record_timestamp":"2024-03-18T22:16:13.633Z"}]}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(content))
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": date(2022, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    }


def test_bilan_simplifie(mocker):
    # Réponse type tronquée de l'API avec 1 dernier bilan simplifié 328847397 JPL LACOSTE
    content = """{"nhits":7,"parameters":{"dataset":"ratios_inpi_bce","q":"siren = 328847397","rows":10,"start":0,"sort":["date_cloture_exercice"],"format":"json","timezone":"UTC"},"records":[{"datasetid":"ratios_inpi_bce","recordid":"d616cd597f1b3352a976e9cf428c49723f2ca4d7","fields":{"marge_brute":22956,"poids_bfr_exploitation_sur_ca":-101.61,"caf_sur_ca":6.644,"ratio_de_vetuste":40.15,"autonomie_financiere":51.963,"date_cloture_exercice":"2022-12-31","marge_ebe":3.84,"ratio_de_liquidite":64.531,"ebe":916,"resultat_net":4858,"taux_d_endettement":108.426,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-365.795,"credit_clients_jours":20.8,"chiffre_d_affaires":23857,"resultat_courant_avant_impots_sur_ca":6.644,"ebit":1585,"type_bilan":"S","couverture_des_interets":0,"credit_fournisseurs_jours":2.653,"rotation_des_stocks_jours":128.264,"siren":"328847397","capacite_de_remboursement":0.729},"record_timestamp":"2024-03-18T22:16:13.633Z"}]}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(content))
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": date(2022, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": None,
    }


def test_echec_ratio_financiers_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    faked_request = mocker.patch("requests.get", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError):
        dernier_exercice_comptable(SIREN)

    faked_request.assert_called_once_with(
        "https://data.economie.gouv.fr/api/records/1.0/search/",
        params={
            "dataset": "ratios_inpi_bce",
            "q": f"siren={SIREN}",
            "sort": "date_cloture_exercice",
        },
        timeout=RATIOS_FINANCIERS_TIMEOUT,
    )
    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert type(args[0]) == Timeout
