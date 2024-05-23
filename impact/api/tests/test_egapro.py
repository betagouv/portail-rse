import json

import pytest
from requests.exceptions import Timeout

from api.egapro import EGAPRO_TIMEOUT
from api.egapro import indicateurs_bdese
from api.egapro import is_index_egapro_published
from api.exceptions import APIError
from api.tests import MockedResponse

SIREN = "123456789"


def test_succes_is_index_egapro_published_avec_declaration(mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":null,"r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""
    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(index_egapro_data))
    )

    assert is_index_egapro_published(SIREN, 2021)
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{SIREN}/2021",
        timeout=EGAPRO_TIMEOUT,
    )


def test_succes_is_index_egapro_published_sans_declaration(mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/889297453/2020
    index_egapro_data = (
        """{"error":"No declaration with siren 889297453 and year 2020"}"""
    )
    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(404, json.loads(index_egapro_data))
    )

    assert not is_index_egapro_published(SIREN, 2020)
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{SIREN}/2020",
        timeout=EGAPRO_TIMEOUT,
    )


def test_echec_is_index_egapro_published_requete_api_invalide(mocker):
    mocker.patch("requests.get", return_value=MockedResponse(400))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(APIError):
        is_index_egapro_published(SIREN, 2023)

    capture_message_mock.assert_called_once_with(
        "Requête invalide sur l'API index EgaPro (is_index_egapro_published)"
    )


def test_echec_is_index_egapro_published_erreur_de_l_api(mocker):
    mocker.patch("requests.get", return_value=MockedResponse(500))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(APIError):
        is_index_egapro_published(SIREN, 2023)

    capture_message_mock.assert_called_once_with(
        "Erreur API index EgaPro (is_index_egapro_published)"
    )


def test_echec_is_index_egapro_published_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    faked_request = mocker.patch("requests.get", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError):
        is_index_egapro_published(SIREN, 2023)

    faked_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{SIREN}/2023",
        timeout=EGAPRO_TIMEOUT,
    )
    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert type(args[0]) == Timeout


@pytest.mark.network
def test_api_fonctionnelle():
    siren = 552032534  # DANONE
    bdese_indicateurs = indicateurs_bdese(siren, 2021)

    assert bdese_indicateurs == {
        "nombre_femmes_plus_hautes_remunerations": 9,
        "objectifs_progression": None,
    }


def test_succes_indicateurs_avec_un_seul_objectif_de_progression(mocker):
    # Example response inspired from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":"plus dans le futur","r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(index_egapro_data))
    )

    bdese_indicateurs = indicateurs_bdese(SIREN, 2021)

    assert bdese_indicateurs == {
        "nombre_femmes_plus_hautes_remunerations": 9,
        "objectifs_progression": "Hautes rémunérations : plus dans le futur",
    }
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{SIREN}/2021",
        timeout=EGAPRO_TIMEOUT,
    )


def test_succes_indicateurs_sans_objectif_de_progression(mocker):
    # Example response inspired from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":null,"r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(index_egapro_data))
    )

    bdese_indicateurs = indicateurs_bdese(SIREN, 2021)

    assert bdese_indicateurs["objectifs_progression"] is None


def test_succes_indicateurs_avec_tous_les_objectifs_de_progression(mocker):
    # Example response inspired from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":"P1"},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":"P2"},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":"P3"},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":"P4"},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":"P5","r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json.loads(index_egapro_data))
    )

    bdese_indicateurs = indicateurs_bdese(SIREN, 2021)

    assert (
        bdese_indicateurs["objectifs_progression"]
        == "Écart taux promotion : P1\nÉcart taux d'augmentation : P2\nÉcart rémunérations : P3\nRetour congé maternité : P4\nHautes rémunérations : P5"
    )


def test_succes_indicateurs_sans_resultat(mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/552032534/1990
    index_egapro_data = (
        """{"error":"No declaration with siren 552032534 and year 1990"}"""
    )

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(404, json.loads(index_egapro_data))
    )

    bdese_indicateurs = indicateurs_bdese(SIREN, 1990)

    assert bdese_indicateurs == {
        "nombre_femmes_plus_hautes_remunerations": None,
        "objectifs_progression": None,
    }


def test_echec_indicateurs_requete_api_invalide(mocker):
    mocker.patch("requests.get", return_value=MockedResponse(400))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(APIError):
        indicateurs_bdese(SIREN, 2023)

    capture_message_mock.assert_called_once_with(
        "Requête invalide sur l'API index EgaPro (indicateurs)"
    )


def test_echec_indicateurs_erreur_de_l_api(mocker):
    mocker.patch("requests.get", return_value=MockedResponse(500))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(APIError):
        indicateurs_bdese(SIREN, 2023)

    capture_message_mock.assert_called_once_with(
        "Erreur API index EgaPro (indicateurs)"
    )


def test_echec_indicateurs_bdese_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    faked_request = mocker.patch("requests.get", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError):
        indicateurs_bdese(SIREN, 2023)

    faked_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{SIREN}/2023",
        timeout=EGAPRO_TIMEOUT,
    )
    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert type(args[0]) == Timeout
