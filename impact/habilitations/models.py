from django.core.exceptions import ObjectDoesNotExist

from entreprises.models import Habilitation


def add_entreprise_to_user(entreprise, user, fonctions):
    Habilitation.objects.create(
        user=user,
        entreprise=entreprise,
        fonctions=fonctions,
    )


def get_habilitation(entreprise, user):
    try:
        return Habilitation.objects.get(
            user=user,
            entreprise=entreprise,
        )
    except ObjectDoesNotExist:
        return
