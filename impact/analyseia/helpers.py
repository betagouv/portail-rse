import json

from reglementations.enums import TitreESRS


def _normalise_titre_esrs(titre_esrs):
    underscored_esrs = titre_esrs[:7].replace(" ", "_")
    return TitreESRS[underscored_esrs].value


def normalise_titre_esrs(titre_esrs, prefixe_ESRS=True):
    titre = _normalise_titre_esrs(titre_esrs)
    if not prefixe_ESRS:
        titre = titre.split("-")[1].strip()
    return titre


def synthese_analyse(entreprise):
    resultat = {
        "phrases_environnement": {},
        "phrases_social": {},
        "phrases_gouvernance": {},
    }
    nb_phrases_pertinentes_detectees = 0
    esrs_thematiques_detectees = set()
    for analyse in entreprise.analyses_ia.all():
        if not analyse.resultat_json:
            break
        for esrs, phrases in json.loads(analyse.resultat_json).items():
            if esrs == "Non ESRS":
                break

            if esrs.startswith("ESRS E"):
                type_esg = "phrases_environnement"
            elif esrs.startswith("ESRS S"):
                type_esg = "phrases_social"
            elif esrs.startswith("ESRS G"):
                type_esg = "phrases_gouvernance"
            titre_esrs = normalise_titre_esrs(esrs, prefixe_ESRS=False)

            if titre_esrs in resultat[type_esg]:
                resultat[type_esg][titre_esrs]["nombre_phrases"] += len(phrases)
            else:
                resultat[type_esg][titre_esrs] = {
                    "titre": titre_esrs,
                    "nombre_phrases": len(phrases),
                    "code_esrs": esrs[5:7],
                }

            esrs_thematiques_detectees.add(titre_esrs)
            nb_phrases_pertinentes_detectees += len(phrases)

    for nom_phase in ("phrases_environnement", "phrases_social", "phrases_gouvernance"):
        resultat[nom_phase] = sorted(
            resultat[nom_phase].values(), key=lambda d: d["titre"]
        )
    resultat["nb_phrases_pertinentes_detectees"] = nb_phrases_pertinentes_detectees
    resultat["nb_documents_analyses"] = entreprise.analyses_ia.count()
    resultat["nb_esrs_thematiques_detectees"] = len(esrs_thematiques_detectees)
    return resultat
