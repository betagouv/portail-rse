from reglementations.views.toutes_reglementations import REGLEMENTATIONS
from vsme.models import RapportVSME


def calculer_metriques_entreprise(entreprise):
    """Calcule les metriques synthetiques pour une entreprise.

    Returns:
        dict: {
            'nombre_reglementations_applicables': int | "?" | None,
            'pourcentage_vsme': int
        }
    """
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes

    # Calcul du nombre de reglementations applicables
    if entreprise.est_etrangere:
        # une entreprise étrangère n'a accès qu'à la VSME
        nombre_reglementations_applicables = None
    elif caracteristiques:
        reglementations_applicables = [
            r for r in REGLEMENTATIONS if r.est_soumis(caracteristiques)
        ]
        nombre_reglementations_applicables = len(reglementations_applicables)
    else:
        nombre_reglementations_applicables = "?"

    # Calcul du pourcentage VSME
    try:
        rapport_vsme = RapportVSME.objects.get(
            entreprise=entreprise,
            annee=entreprise.dernier_exercice_clos.date_cloture.year,
        )
        pourcentage_vsme = rapport_vsme.progression()["pourcent"]
    except RapportVSME.DoesNotExist:
        pourcentage_vsme = 0

    return {
        "nombre_reglementations_applicables": nombre_reglementations_applicables,
        "pourcentage_vsme": pourcentage_vsme,
    }
