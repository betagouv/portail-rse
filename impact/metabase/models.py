from django.db import models

from entreprises.models import RAISON_SOCIALE_MAX_LENGTH


class Entreprise(models.Model):
    siren = models.CharField(max_length=9, unique=True)
    effectif = models.CharField(max_length=9, null=True)
    bdese_accord = models.BooleanField(default=False)
    raison_sociale = models.CharField(max_length=RAISON_SOCIALE_MAX_LENGTH)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.siren} {self.raison_sociale}"
