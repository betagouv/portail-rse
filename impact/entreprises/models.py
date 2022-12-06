from django.conf import settings
from django.db import models

RAISON_SOCIALE_MAX_LENGTH = 250


class Entreprise(models.Model):
    EFFECTIF_CHOICES = [
        ("petit", "moins de 50"),
        ("moyen", "entre 50 et 300"),
        ("grand", "entre 301 et 499"),
        ("sup500", "500 et plus"),
    ]

    siren = models.CharField(max_length=9, unique=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    effectif = models.CharField(
        max_length=9,
        choices=EFFECTIF_CHOICES,
        help_text="Vérifiez et confirmez le nombre de salariés",
    )
    bdese_accord = models.BooleanField(default=False)
    raison_sociale = models.CharField(max_length=RAISON_SOCIALE_MAX_LENGTH, default="")

    def __str__(self):
        return f"{self.siren} {self.raison_sociale}"
