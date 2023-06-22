from django.db import models

from entreprises.models import DENOMINATION_MAX_LENGTH
from habilitations.models import FONCTIONS_MAX_LENGTH


class Utilisateur(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoute_le = models.DateTimeField()
    modifie_le = models.DateTimeField()
    reception_actualites = models.BooleanField()
    email_confirme = models.BooleanField()


class Entreprise(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoutee_le = models.DateTimeField()
    modifiee_le = models.DateTimeField()
    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)

    effectif = models.CharField(max_length=9, null=True)
    bdese_accord = models.BooleanField(null=True)
    nombre_utilisateurs = models.IntegerField()

    utilisateurs = models.ManyToManyField(Utilisateur, through="Habilitation")

    def __str__(self):
        return f"{self.siren} {self.denomination}"


class Habilitation(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fonctions = models.CharField(max_length=FONCTIONS_MAX_LENGTH, null=True)
    confirmee_le = models.DateTimeField(null=True)
