from django.db import models

from entreprises.models import DENOMINATION_MAX_LENGTH


class Entreprise(models.Model):
    siren = models.CharField(max_length=9, unique=True)
    effectif = models.CharField(max_length=9, null=True)
    bdese_accord = models.BooleanField(default=False)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.siren} {self.denomination}"
