from django import template

register = template.Library()


@register.filter
def a_une_correspondance(analyses_ia, champs_ids):
    """Indique si au moins un résultat des analyses IA correspond à l'un des champs donnés."""
    if isinstance(champs_ids, str):
        champs_ids = [champs_ids]
    return any(
        resultat["champ_id"] in champs_ids
        for analyse in analyses_ia
        for resultat in analyse["resultats"]
    )


@register.filter
def resultats_correspondants(resultats, champs_ids):
    """Filtre les résultats d'une analyse pour ne garder que ceux correspondant à l'un des champs donnés."""
    if isinstance(champs_ids, str):
        champs_ids = [champs_ids]
    return [resultat for resultat in resultats if resultat["champ_id"] in champs_ids]
