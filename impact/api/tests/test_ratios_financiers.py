import json
from datetime import date

import pytest

from api.ratios_financiers import dernier_exercice_comptable
from entreprises.models import CaracteristiquesAnnuelles

SIREN = "123456789"


class MockedResponse:
    def __init__(self, status_code, content=""):
        self.status_code = status_code
        self.content = content

    def json(self):
        return json.loads(self.content)


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
        "requests.get", return_value=MockedResponse(200, content)
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": None,
        "tranche_chiffre_affaires": None,
        "tranche_chiffre_affaires_consolide": None,
    }


def test_pas_de_bilan_consolide(mocker):
    # Réponse type de l'API avec 2 derniers bilans complets et pas de bilan consolidé 511278533 3MEDIA
    content = """{"nhits": 6, "parameters": {"dataset": "ratios_inpi_bce", "q": "siren = 511278533", "rows": 10, "start": 0, "sort": ["date_cloture_exercice"], "format": "json", "timezone": "UTC"}, "records": [{"datasetid": "ratios_inpi_bce", "recordid": "55580925dd686878088d827f4712e2f3aef7cd83", "fields": {"marge_brute": 15711568, "poids_bfr_exploitation_sur_ca": 5.575, "caf_sur_ca": -9.299, "ratio_de_vetuste": 14.647, "autonomie_financiere": -21.002, "date_cloture_exercice": "2021-12-31", "marge_ebe": -9.153, "ratio_de_liquidite": 82.502, "ebe": -1438048, "resultat_net": -1147009, "taux_d_endettement": -0.552, "confidentiality": "Public", "poids_bfr_exploitation_sur_ca_jours": 20.07, "credit_clients_jours": 42.966, "chiffre_d_affaires": 15711568, "resultat_courant_avant_impots_sur_ca": -7.309, "ebit": -1159715, "type_bilan": "C", "couverture_des_interets": -0.042, "credit_fournisseurs_jours": 99.673, "rotation_des_stocks_jours": 0.0, "siren": "511278533", "capacite_de_remboursement": 0.0}, "record_timestamp": "2024-03-18T22:16:13.633Z"}, {"datasetid": "ratios_inpi_bce", "recordid": "189d6361b965075979ea4af728292e87288be8a3", "fields": {"marge_brute": 17188502, "poids_bfr_exploitation_sur_ca": 14.671, "caf_sur_ca": 5.198, "ratio_de_vetuste": 17.642, "autonomie_financiere": 30.723, "date_cloture_exercice": "2020-12-31", "marge_ebe": 9.014, "ratio_de_liquidite": 148.939, "ebe": 1549389, "resultat_net": 760061, "taux_d_endettement": 0.395, "confidentiality": "Public", "poids_bfr_exploitation_sur_ca_jours": 52.815, "credit_clients_jours": 16.649, "chiffre_d_affaires": 1718850200, "resultat_courant_avant_impots_sur_ca": 8.069, "ebit": 1390231, "type_bilan": "C", "couverture_des_interets": 0.495, "credit_fournisseurs_jours": 60.076, "rotation_des_stocks_jours": 0.0, "siren": "511278533", "capacite_de_remboursement": 0.008}, "record_timestamp": "2024-03-18T22:16:13.633Z"}]}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, content)
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": date(2021, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_chiffre_affaires_consolide": None,
    }


def test_bilan_complet_et_bilan_consolide(mocker):
    # Réponse type de l'API avec 1 dernier bilan complet et 1 dernier bilan consolidé 552032534 DANONE
    content = """{"nhits":13,"parameters":{"dataset":"ratios_inpi_bce","q":"siren = 552032534","rows":10,"start":0,"sort":["date_cloture_exercice"],"format":"json","timezone":"UTC"},"records":[{"datasetid":"ratios_inpi_bce","recordid":"a911bf2fce0b993b8827a7bbc4d3114c0ed8021c","fields":{"marge_brute":11521000000,"poids_bfr_exploitation_sur_ca":46.938,"caf_sur_ca":5.791,"autonomie_financiere":179.52,"date_cloture_exercice":"2022-12-31","marge_ebe":13.756,"ratio_de_liquidite":0,"ebe":3340000000,"resultat_net":0,"taux_d_endettement":20.366,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":168.977,"credit_clients_jours":0,"chiffre_d_affaires":24281000000,"resultat_courant_avant_impots_sur_ca":8.216,"ebit":2257000000,"type_bilan":"K","couverture_des_interets":18.443,"credit_fournisseurs_jours":57.275,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":11.796},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"714b8ab05369c061f2ac2ac719a6f17832a4761f","fields":{"marge_brute":635000000,"poids_bfr_exploitation_sur_ca":-195.433,"caf_sur_ca":602.205,"ratio_de_vetuste":38.298,"autonomie_financiere":47.213,"date_cloture_exercice":"2022-12-31","marge_ebe":60,"ratio_de_liquidite":21.361,"ebe":381000000,"resultat_net":3674000000,"taux_d_endettement":92.375,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-703.559,"credit_clients_jours":0,"chiffre_d_affaires":635000000,"resultat_courant_avant_impots_sur_ca":609.606,"ebit":-137000000,"type_bilan":"C","couverture_des_interets":60.892,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":3.865},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"591803b887dd4cef6f6c2b6e9d0a69f2e548edda","fields":{"marge_brute":635000000,"poids_bfr_exploitation_sur_ca":-246.142,"caf_sur_ca":602.205,"ratio_de_vetuste":43.182,"autonomie_financiere":50.901,"date_cloture_exercice":"2021-12-31","marge_ebe":60,"ratio_de_liquidite":18.715,"ebe":381000000,"resultat_net":3674000000,"taux_d_endettement":85.681,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-886.11,"credit_clients_jours":0,"chiffre_d_affaires":635000000,"resultat_courant_avant_impots_sur_ca":609.606,"ebit":-137000000,"type_bilan":"C","couverture_des_interets":62.205,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":3.865},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"cdcf936091d4efabbc761e8f77bbb714bf3e9450","fields":{"marge_brute":11521000000,"poids_bfr_exploitation_sur_ca":34.451,"caf_sur_ca":10.642,"autonomie_financiere":38.254,"date_cloture_exercice":"2021-12-31","marge_ebe":47.449,"ratio_de_liquidite":0,"ebe":11521000000,"resultat_net":1992000000,"taux_d_endettement":96.017,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":124.023,"credit_clients_jours":0,"chiffre_d_affaires":24281000000,"resultat_courant_avant_impots_sur_ca":8.216,"ebit":2257000000,"type_bilan":"K","couverture_des_interets":2.274,"credit_fournisseurs_jours":93.997,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":6.418},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"c5b8edd1487b28bc97753223d2b88bb4bef06a97","fields":{"marge_brute":25287000000,"poids_bfr_exploitation_sur_ca":37.466,"caf_sur_ca":15.217,"autonomie_financiere":38.008,"date_cloture_exercice":"2020-12-31","marge_ebe":100,"ratio_de_liquidite":0,"ebe":25287000000,"resultat_net":2028000000,"taux_d_endettement":25.95,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":134.877,"credit_clients_jours":0,"chiffre_d_affaires":25287000000,"resultat_courant_avant_impots_sur_ca":11.338,"ebit":21441000000,"type_bilan":"K","couverture_des_interets":0.743,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":1.163},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"460b62d9e7d87f8a18f27a4084e620bcc9cbec6d","fields":{"marge_brute":622000000,"poids_bfr_exploitation_sur_ca":-935.048,"caf_sur_ca":315.916,"ratio_de_vetuste":53.333,"autonomie_financiere":39.603,"date_cloture_exercice":"2020-12-31","marge_ebe":58.199,"ratio_de_liquidite":5.741,"ebe":362000000,"resultat_net":1931000000,"taux_d_endettement":97.867,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-3366.174,"credit_clients_jours":0,"chiffre_d_affaires":622000000,"resultat_courant_avant_impots_sur_ca":304.18,"ebit":-130000000,"type_bilan":"C","couverture_des_interets":70.442,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":6.75},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"cd3d58866657dc59caa7c72c6386eac5478b1275","fields":{"marge_brute":25287000,"poids_bfr_exploitation_sur_ca":37465.892,"caf_sur_ca":-3124.661,"autonomie_financiere":38.008,"date_cloture_exercice":"2019-12-31","marge_ebe":100,"ratio_de_liquidite":0,"ebe":25287000,"resultat_net":2028000000,"taux_d_endettement":0,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":134877.21,"credit_clients_jours":0,"chiffre_d_affaires":25287000,"resultat_courant_avant_impots_sur_ca":11.338,"ebit":3237000,"type_bilan":"K","couverture_des_interets":0.743,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":0},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"5a06ad53ff77e062d681b47961758dad5cf13df1","fields":{"marge_brute":593000000,"poids_bfr_exploitation_sur_ca":-667.116,"caf_sur_ca":54.469,"ratio_de_vetuste":36.842,"autonomie_financiere":37.761,"date_cloture_exercice":"2019-12-31","marge_ebe":50.253,"ratio_de_liquidite":8.532,"ebe":298000000,"resultat_net":471000000,"taux_d_endettement":119.827,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-2401.619,"credit_clients_jours":167.454,"chiffre_d_affaires":593000000,"resultat_courant_avant_impots_sur_ca":67.791,"ebit":-163000000,"type_bilan":"C","couverture_des_interets":5.034,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":48.105},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"aa41f538b49e467c908cfa9b9486ecc3d7bfc7e9","fields":{"marge_brute":666000000,"poids_bfr_exploitation_sur_ca":-342.342,"caf_sur_ca":104.354,"date_cloture_exercice":"2018-12-31","marge_ebe":56.907,"ratio_de_liquidite":11.94,"ebe":379000000,"resultat_net":899000000,"taux_d_endettement":120.272,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-1232.432,"credit_clients_jours":0,"chiffre_d_affaires":666000000,"resultat_courant_avant_impots_sur_ca":119.97,"ebit":-62000000,"type_bilan":"C","couverture_des_interets":77.309,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":23.681},"record_timestamp":"2024-03-18T22:16:13.633Z"},{"datasetid":"ratios_inpi_bce","recordid":"6fff26949678c6967ce63b5d60ee7f6eaf33d79d","fields":{"marge_brute":24812000000,"poids_bfr_exploitation_sur_ca":36.249,"caf_sur_ca":16.661,"autonomie_financiere":32.827,"date_cloture_exercice":"2018-12-31","marge_ebe":100,"ratio_de_liquidite":0,"ebe":24812000000,"resultat_net":2559000000,"taux_d_endettement":0,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":130.495,"credit_clients_jours":0,"chiffre_d_affaires":24812000000,"resultat_courant_avant_impots_sur_ca":13.268,"ebit":0,"type_bilan":"K","couverture_des_interets":0,"rotation_des_stocks_jours":0,"siren":"552032534","capacite_de_remboursement":0},"record_timestamp":"2024-03-18T22:16:13.633Z"}]}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, content)
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": date(2022, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    }


def test_bilan_simplifie(mocker):
    # Réponse type de l'API avec 1 dernier bilan simplifié 328847397 JPL LACOSTE
    content = """{"nhits":7,"parameters":{"dataset":"ratios_inpi_bce","q":"siren = 328847397","rows":10,"start":0,"sort":["date_cloture_exercice"],"format":"json","timezone":"UTC"},"records":[{"datasetid":"ratios_inpi_bce","recordid":"d616cd597f1b3352a976e9cf428c49723f2ca4d7","fields":{"marge_brute":22956,"poids_bfr_exploitation_sur_ca":-101.61,"caf_sur_ca":6.644,"ratio_de_vetuste":40.15,"autonomie_financiere":51.963,"date_cloture_exercice":"2022-12-31","marge_ebe":3.84,"ratio_de_liquidite":64.531,"ebe":916,"resultat_net":4858,"taux_d_endettement":108.426,"confidentiality":"Public","poids_bfr_exploitation_sur_ca_jours":-365.795,"credit_clients_jours":20.8,"chiffre_d_affaires":23857,"resultat_courant_avant_impots_sur_ca":6.644,"ebit":1585,"type_bilan":"S","couverture_des_interets":0,"credit_fournisseurs_jours":2.653,"rotation_des_stocks_jours":128.264,"siren":"328847397","capacite_de_remboursement":0.729},"record_timestamp":"2024-03-18T22:16:13.633Z"}]}"""
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, content)
    )

    data = dernier_exercice_comptable(SIREN)

    assert data == {
        "date_cloture_exercice": date(2022, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": None,
    }
