from django.http import JsonResponse
from django.views.decorators.http import require_GET

from entreprises.models import Entreprise
from poc_lee.apis_figees import apis_externes_figees
from poc_lee.auth import token_lee_requis
from reglementations.views.base import ReglementationStatus
from reglementations.views.toutes_reglementations import calcule_reglementations

STATUTS = {
    ReglementationStatus.STATUS_A_ACTUALISER: "a-actualiser",
    ReglementationStatus.STATUS_EN_COURS: "en-cours",
    ReglementationStatus.STATUS_A_JOUR: "a-jour",
    ReglementationStatus.STATUS_SOUMIS: "soumis",
    ReglementationStatus.STATUS_NON_SOUMIS: "non-soumis",
    ReglementationStatus.STATUS_RECOMMANDE: "recommande",
    ReglementationStatus.STATUS_INCALCULABLE: "incalculable",
}


def entreprise_qualifiee(siren):
    entreprise = Entreprise.objects.filter(identifiant=siren).first()
    if not entreprise:
        return JsonResponse({"erreur": "entreprise-inconnue"}, status=404)
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    if not caracteristiques:
        return JsonResponse({"erreur": "entreprise-non-qualifiee"}, status=404)
    return entreprise, caracteristiques


@token_lee_requis
@require_GET
def obligations(request, siren):
    resultat = entreprise_qualifiee(siren)
    if isinstance(resultat, JsonResponse):
        return resultat
    entreprise, caracteristiques = resultat
    with apis_externes_figees():
        reglementations = calcule_reglementations(caracteristiques)
    return JsonResponse(
        {
            "siren": entreprise.identifiant,
            "denomination": entreprise.denomination,
            "obligations": [
                {
                    "id": r["reglementation"].id,
                    "titre": r["reglementation"].title,
                    "statut": STATUTS[r["status"].status],
                    "detail": r["status"].status_detail,
                    "url": r["reglementation"].more_info_url,
                }
                for r in reglementations
            ],
        }
    )
