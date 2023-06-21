from django.db import models

from entreprises.models import DENOMINATION_MAX_LENGTH
from habilitations.models import FONCTIONS_MAX_LENGTH


class Utilisateur(models.Model):
    impact_id = models.BigIntegerField(unique=True)
    cree_le = models.DateTimeField()
    modifie_le = models.DateTimeField()
    reception_actualites = models.BooleanField()
    email_valide = models.BooleanField()


class Entreprise(models.Model):
    impact_id = models.BigIntegerField(
        unique=True, null=True
    )  # null=True peut être temporaire mais nécessaire pour ajouter le champ sur le modèle existant
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    siren = models.CharField(max_length=9, unique=True)
    effectif = models.CharField(max_length=9, null=True)
    bdese_accord = models.BooleanField(null=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)
    nombre_utilisateurs = models.IntegerField(
        null=True
    )  # null=True peut être temporaire mais nécessaire pour ajouter le champ sur le modèle existant
    utilisateurs = models.ManyToManyField(Utilisateur, through="Habilitation")

    def __str__(self):
        return f"{self.siren} {self.denomination}"


class Habilitation(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fonctions = models.CharField(max_length=FONCTIONS_MAX_LENGTH, null=True)
    confirmee_le = models.DateTimeField(null=True)
