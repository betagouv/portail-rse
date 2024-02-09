from django.urls import reverse

from reglementations.views.csrd import CSRDReglementation


def test_reglementation_info():
    info = CSRDReglementation.info()

    assert info["title"] == "Rapport de durabilité - Directive CSRD"
    assert info["more_info_url"] == reverse("reglementations:fiche_csrd")
