from datetime import datetime, timezone

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from utils.models import TimestampedModel

RAISON_SOCIALE_MAX_LENGTH = 250
FONCTIONS_MAX_LENGTH = 250


class Entreprise(TimestampedModel):
    EFFECTIF_CHOICES = [
        ("petit", "moins de 50"),
        ("moyen", "entre 50 et 300"),
        ("grand", "entre 301 et 499"),
        ("sup500", "plus de 500"),
    ]

    siren = models.CharField(max_length=9, unique=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Habilitation")
    effectif = models.CharField(
        max_length=9,
        choices=EFFECTIF_CHOICES,
        help_text="Vérifiez et confirmez le nombre de salariés",
    )
    bdese_accord = models.BooleanField(default=False)
    raison_sociale = models.CharField(max_length=RAISON_SOCIALE_MAX_LENGTH, default="")

    def __str__(self):
        return f"{self.siren} {self.raison_sociale}"


class Habilitation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fonctions = models.CharField(
        verbose_name="Fonction(s) dans la société",
        max_length=FONCTIONS_MAX_LENGTH,
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(null=True)

    def confirm(self):
        self.confirmed_at = datetime.now(timezone.utc)

    @property
    def is_confirmed(self):
        return bool(self.confirmed_at)


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
