from datetime import datetime
from datetime import timezone

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from entreprises.models import Entreprise
from reglementations.models import get_all_personal_bdese
from reglementations.models import has_official_bdese
from utils.models import TimestampedModel

FONCTIONS_MIN_LENGTH = 3
FONCTIONS_MAX_LENGTH = 250


class Habilitation(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fonctions = models.CharField(
        verbose_name="Fonction(s) dans la société",
        max_length=FONCTIONS_MAX_LENGTH,
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(
        verbose_name="Confirmée le",
        null=True,
    )

    def __str__(self):
        return f"Habilitation : {self.entreprise}, {self.user}"

    def confirm(self):
        self.confirmed_at = datetime.now(timezone.utc)
        if not has_official_bdese(self.entreprise):
            for bdese in get_all_personal_bdese(self.entreprise, self.user):
                bdese.officialize()

    def unconfirm(self):
        self.confirmed_at = None

    @property
    def is_confirmed(self):
        return bool(self.confirmed_at)


def attach_user_to_entreprise(user, entreprise, fonctions):
    return Habilitation.objects.create(
        user=user,
        entreprise=entreprise,
        fonctions=fonctions,
    )


def detach_user_from_entreprise(user, entreprise):
    get_habilitation(user, entreprise).delete()


def get_habilitation(user, entreprise):
    return Habilitation.objects.get(
        user=user,
        entreprise=entreprise,
    )


def is_user_attached_to_entreprise(user, entreprise):
    try:
        get_habilitation(user, entreprise)
        return True
    except (ObjectDoesNotExist, TypeError):
        return False


def is_user_habilited_on_entreprise(user, entreprise):
    return (
        is_user_attached_to_entreprise(user, entreprise)
        and get_habilitation(user, entreprise).is_confirmed
    )
