from django.db import models

from entreprises.models import DENOMINATION_MAX_LENGTH
from habilitations.models import FONCTIONS_MAX_LENGTH


class Utilisateur(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoute_le = models.DateTimeField()
    modifie_le = models.DateTimeField()
    connecte_le = models.DateField(null=True)
    reception_actualites = models.BooleanField()
    email_confirme = models.BooleanField()

    nombre_entreprises = models.IntegerField()


class Entreprise(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoutee_le = models.DateTimeField()
    modifiee_le = models.DateTimeField()
    siren = models.CharField(max_length=9, unique=True)
    denomination = models.CharField(max_length=DENOMINATION_MAX_LENGTH)

    date_cloture_exercice = models.DateField(null=True)
    date_derniere_qualification = models.DateField(null=True)
    categorie_juridique = models.CharField(max_length=50, null=True)
    est_cotee = models.BooleanField(null=True)
    appartient_groupe = models.BooleanField(null=True)
    societe_mere_en_france = models.BooleanField(null=True)
    comptes_consolides = models.BooleanField(null=True)
    effectif = models.CharField(max_length=9, null=True)
    effectif_permanent = models.CharField(max_length=9, null=True)
    effectif_outre_mer = models.CharField(max_length=9, null=True)
    effectif_groupe = models.CharField(max_length=9, null=True)
    effectif_groupe_permanent = models.CharField(max_length=9, null=True)
    tranche_chiffre_affaires = models.CharField(max_length=9, null=True)
    tranche_bilan = models.CharField(max_length=9, null=True)
    tranche_chiffre_affaires_consolide = models.CharField(max_length=9, null=True)
    tranche_bilan_consolide = models.CharField(max_length=9, null=True)
    bdese_accord = models.BooleanField(null=True)
    systeme_management_energie = models.BooleanField(null=True)

    nombre_utilisateurs = models.IntegerField()

    utilisateurs = models.ManyToManyField(Utilisateur, through="Habilitation")

    def __str__(self):
        return f"{self.siren} {self.denomination}"


class Habilitation(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoutee_le = models.DateTimeField()
    modifiee_le = models.DateTimeField()
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fonctions = models.CharField(max_length=FONCTIONS_MAX_LENGTH, null=True)
    confirmee_le = models.DateTimeField(null=True)
