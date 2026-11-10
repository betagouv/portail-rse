import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from entreprises.models import Entreprise
from poc_lee.apis_figees import apis_externes_figees
from poc_lee.auth import token_lee_requis
from poc_lee.models import PreremplissageLee
from reglementations.views.base import ReglementationStatus
from reglementations.views.toutes_reglementations import calcule_reglementations
from vsme.forms.vsme import THEMATIQUES_DURABILITE
from vsme.models import RapportVSME
from vsme.models import validate_annee_rapport

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


def parse_pratiques(body):
    if not isinstance(body, dict):
        return None
    annee = body.get("annee")
    pratiques = body.get("pratiques")
    if not isinstance(annee, int) or isinstance(annee, bool):
        return None
    try:
        validate_annee_rapport(annee)
    except ValidationError:
        return None
    if not isinstance(pratiques, list) or not 1 <= len(pratiques) <= 10:
        return None
    resultat = []
    for pratique in pratiques:
        if not isinstance(pratique, dict):
            return None
        thematique = pratique.get("thematique")
        description = pratique.get("description")
        if thematique not in THEMATIQUES_DURABILITE:
            return None
        if not isinstance(description, str):
            return None
        description = description.strip()
        if not description or len(description) > 2000:
            return None
        resultat.append((thematique, description))
    if len({thematique for thematique, _ in resultat}) != len(resultat):
        return None
    return annee, resultat


@token_lee_requis
@require_POST
def preremplissages(request, siren):
    resultat = entreprise_qualifiee(siren)
    if isinstance(resultat, JsonResponse):
        return resultat
    entreprise, _ = resultat
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        body = None
    parse = parse_pratiques(body)
    if parse is None:
        return JsonResponse({"erreur": "requete-invalide"}, status=400)
    annee, pratiques = parse
    with transaction.atomic():
        rapport, _ = RapportVSME.objects.get_or_create(
            entreprise=entreprise, annee=annee
        )
        donnees = {
            "B2-26": {
                "declaration_durabilite": {
                    thematique: {"pratiques": True} for thematique, _ in pratiques
                }
            },
            "C2-48": {
                "description_durabilite": {
                    thematique: {"description_pratiques": description}
                    for thematique, description in pratiques
                }
            },
        }
        for schema_id, data in donnees.items():
            PreremplissageLee.objects.update_or_create(
                rapport_vsme=rapport, schema_id=schema_id, defaults={"data": data}
            )
    return JsonResponse(
        {
            "rapport_url": request.build_absolute_uri(
                reverse("vsme:exigence_de_publication_vsme", args=[rapport.id, "B2"])
            )
        },
        status=201,
    )
