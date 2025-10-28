import json
import os
from uuid import uuid4

import django.db.models as models
from django.core.files.storage import default_storage

from utils.models import TimestampedModel


# TODO : refactor ?


class AnalyseIAQuerySet(models.QuerySet):
    def reussies(self):
        return self.filter(etat__exact="success")

    def non_lancees(self):
        return self.filter(etat__isnull=True)


def select_storage():
    # Utiliser un autre storage que celui par défaut ne permet pas de le modifier dans les tests
    # https://code.djangoproject.com/ticket/36269
    return default_storage


def upload_path(instance, filename):
    return f"analyse_ia/{str(uuid4())}.pdf"


class AnalyseIA(TimestampedModel):
    fichier = models.FileField(storage=select_storage, upload_to=upload_path)
    nom = models.CharField(max_length=255, verbose_name="nom d'origine")
    resultat_json = models.JSONField(
        null=True, blank=True, verbose_name="résultat de l'analyse IA au format JSON"
    )
    etat = models.CharField(
        max_length=144,
        null=True,
        blank=True,
        verbose_name="dernier état connu du traitement d'analyse IA envoyé par le serveur IA",
    )
    message = models.CharField(
        max_length=144,
        null=True,
        blank=True,
        verbose_name="éventuel message précisant l'état envoyé par le serveur IA",
    )

    class Meta:
        verbose_name = "document analyse IA"
        verbose_name_plural = "documents analyse IA"

    objects = AnalyseIAQuerySet.as_manager()

    def __str__(self):
        return f"AnalyseIA {self.id} - {self.nom}"

    def save(self, *args, **kwargs):
        # Enregistre le nom d'origine du fichier avant qu'il ne soit modifié lors du stockage sur le S3
        if not self.nom:
            self.nom = os.path.basename(self.fichier.name)
        super().save(*args, **kwargs)

    @property
    def nombre_de_phrases_pertinentes(self):
        try:
            data = json.loads(self.resultat_json)
        except TypeError:  # cas d'un fichier non traité
            return 0
        quantite = 0
        for esrs, phrases in data.items():
            if "Non ESRS" not in esrs:
                quantite += len(phrases)
        return quantite

    @property
    def entreprise(self):
        if self.entreprises.count():
            return self.entreprises.first()
        else:
            return self.rapports_csrd.first().entreprise
