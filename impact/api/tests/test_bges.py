import json

import pytest

from api.bges import last_reporting_year

SIREN = "123456789"


class MockedResponse:
    def __init__(self, status_code, content=""):
        self.status_code = status_code
        self.content = content

    def json(self):
        return json.loads(self.content)


def test_une_seule_annee_de_publication_trouvee(mocker):
    # Réponse type de l'API interne à bilans-ges.ademe.fr/api/inventories
    # les données correspondant aux clefs inventoryResponsibleContact, inventoryEntity, entity, hydra:view et hydra:search ont été supprimées
    data = """{"@context": "/api/contexts/Inventory", "@id": "/api/inventories", "@type": "hydra:Collection", "hydra:totalItems": 1, "hydra:member": [{"@id": "/api/inventories/93bd590a-b1cd-11ed-8fce-005056b7acd1", "@type": "Inventory", "id": "93bd590a-b1cd-11ed-8fce-005056b7acd1", "identitySheet": {"@id": "/api/inventory_identity_sheets/93bd590a-b1cd-11ed-8fce-005056b7acd1", "@type": "InventoryIdentitySheet", "reportingYear": 2021, "APECode": {"@id": "/api/ape_codes/8220Z", "@type": "ape_codes", "id": "8220Z", "label": "Activités de centres d'appels"}, "consolidationMode": 0, "dpef": false, "creatorEmail": "address@domain.example", "requiredPCAET": false, "diagnosticIncludedPCAET": false, "actionPlanPCAET": null, "collectivityType": null, "turnover": null, "diagDecarbonAction": null, "isCollectivityPcaetSubmitted": false}, "inventoryEntity": {}, "entity": {}, "createdAt": "2023-02-21T10:53:21+00:00", "inspiring": false, "inventoryResponsibleContact": {}, "publication": {"@id": "/api/inventory_publications/93bd590a-b1cd-11ed-8fce-005056b7acd1", "@type": "InventoryPublication", "status": "valide", "publicatedAt": "2022-05-12T15:57:19+00:00"}, "declaration": null, "associatedSiren": [], "scope3Visible": true, "isV4": true}], "hydra:view": {}, "hydra:search": {}}"""

    faked_request = mocker.patch("requests.get", return_value=MockedResponse(200, data))

    year = last_reporting_year(SIREN)

    assert year == 2021
    faked_request.assert_called_once_with(
        "https://bilans-ges.ademe.fr/api/inventories",
        params={"page": "1", "itemsPerPage": "11", "entity.siren": SIREN},
    )


def test_aucune_annee_de_publication(mocker):
    # Réponse type de l'API interne à bilans-ges.ademe.fr/api/inventories
    # les données correspondant aux clefs inventoryResponsibleContact, inventoryEntity, entity, hydra:view et hydra:search ont été supprimées
    data = """{"@context": "/api/contexts/Inventory", "@id": "/api/inventories", "@type": "hydra:Collection", "hydra:totalItems": 0, "hydra:member": [], "hydra:view": {}, "hydra:search": {}}"""
    faked_request = mocker.patch("requests.get", return_value=MockedResponse(200, data))

    year = last_reporting_year(SIREN)

    assert year == None
    faked_request.assert_called_once_with(
        "https://bilans-ges.ademe.fr/api/inventories",
        params={"page": "1", "itemsPerPage": "11", "entity.siren": SIREN},
    )


def test_deux_annees_de_publication_trouvees(mocker):
    # Réponse type de l'API interne à bilans-ges.ademe.fr/api/inventories
    # les données correspondant aux clefs associatedSiren, inventoryResponsibleContact, inventoryEntity, entity, hydra:view et hydra:search ont été supprimées
    # années considérées : 2022 et 2018
    data = r"""{"@context":"\/api\/contexts\/Inventory","@id":"\/api\/inventories","@type":"hydra:Collection","hydra:totalItems":2,"hydra:member":[{"@id":"\/api\/inventories\/f4386e8f-386b-4a48-bae4-7a5496a008d7","@type":"Inventory","id":"f4386e8f-386b-4a48-bae4-7a5496a008d7","identitySheet":{"@id":"\/api\/inventory_identity_sheets\/f4386e8f-386b-4a48-bae4-7a5496a008d7","@type":"InventoryIdentitySheet","reportingYear":2022,"APECode":{"@id":"\/api\/ape_codes\/7010Z","@type":"ape_codes","id":"7010Z","label":"Activités des sièges sociaux"},"consolidationMode":0,"dpef":true,"requiredPCAET":null,"diagnosticIncludedPCAET":null,"actionPlanPCAET":null,"collectivityType":null,"turnover":280900000,"diagDecarbonAction":null,"isCollectivityPcaetSubmitted":false},"inventoryEntity":{},"entity":{},"createdAt":"2023-09-11T13:26:35+00:00","inspiring":false,"inventoryResponsibleContact":{},"publication":{"@id":"\/api\/inventory_publications\/f4386e8f-386b-4a48-bae4-7a5496a008d7","@type":"InventoryPublication","status":"a-traiter","publicatedAt":"2023-12-14T13:19:36+00:00"},"declaration":"\/api\/inventory_declarations\/f4386e8f-386b-4a48-bae4-7a5496a008d7","associatedSiren":[],"scope3Visible":true,"isV4":null},{"@id":"\/api\/inventories\/9395ec53-b1cd-11ed-8fce-005056b7acd1","@type":"Inventory","id":"9395ec53-b1cd-11ed-8fce-005056b7acd1","identitySheet":{"@id":"\/api\/inventory_identity_sheets\/9395ec53-b1cd-11ed-8fce-005056b7acd1","@type":"InventoryIdentitySheet","reportingYear":2018,"APECode":{"@id":"\/api\/ape_codes\/7010Z","@type":"ape_codes","id":"7010Z","label":"Activités des sièges sociaux"},"consolidationMode":0,"dpef":false,"creatorEmail":"address@domain.example","requiredPCAET":false,"diagnosticIncludedPCAET":false,"actionPlanPCAET":null,"collectivityType":null,"turnover":null,"diagDecarbonAction":null,"isCollectivityPcaetSubmitted":false},"inventoryEntity":{},"entity":{},"createdAt":"2023-02-21T10:53:21+00:00","inspiring":false,"inventoryResponsibleContact":{},"publication":{"@id":"\/api\/inventory_publications\/9395ec53-b1cd-11ed-8fce-005056b7acd1","@type":"InventoryPublication","status":"a-traiter","publicatedAt":"2019-12-06T14:57:16+00:00"},"declaration":"\/api\/inventory_declarations\/9395ec53-b1cd-11ed-8fce-005056b7acd1","associatedSiren":[],"scope3Visible":true,"isV4":true}],"hydra:view":{},"hydra:search":{}}"""
    faked_request = mocker.patch("requests.get", return_value=MockedResponse(200, data))

    year = last_reporting_year(SIREN)

    assert year == 2022
    faked_request.assert_called_once_with(
        "https://bilans-ges.ademe.fr/api/inventories",
        params={"page": "1", "itemsPerPage": "11", "entity.siren": SIREN},
    )


@pytest.mark.parametrize("code_http", [400, 500])
def test_echec_erreur_de_l_api(code_http, mocker):
    mocker.patch("requests.get", return_value=MockedResponse(code_http))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    year = last_reporting_year(SIREN)

    assert year is None
    capture_message_mock.assert_called_once_with(
        "Erreur API bilans-ges (" + SIREN + ")"
    )


def test_echec_l_api_a_change(mocker):
    data = """{"@context": "/api/contexts/Inventory", "autre": "structure"}"""
    mocker.patch("requests.get", return_value=MockedResponse(200, data))
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    year = last_reporting_year(SIREN)

    assert year is None
    assert capture_exception_mock.called_once


@pytest.mark.network
def test_api_fonctionnelle():
    siren = 511278533  # 3MEDIA

    year = last_reporting_year(siren)

    assert year >= 2021
