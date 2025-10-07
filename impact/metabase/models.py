from django.db import models

from entreprises.models import DENOMINATION_MAX_LENGTH
from habilitations.models import FONCTIONS_MAX_LENGTH
from utils.models import TimestampedModel


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
    pays = models.CharField(max_length=50, null=True)
    code_NAF = models.CharField(max_length=6, null=True)
    est_interet_public = models.BooleanField(null=True)
    est_cotee = models.BooleanField(null=True)
    appartient_groupe = models.BooleanField(null=True)
    est_societe_mere = models.BooleanField(null=True)
    societe_mere_en_france = models.BooleanField(null=True)
    comptes_consolides = models.BooleanField(null=True)
    effectif = models.CharField(max_length=9, null=True)
    effectif_securite_sociale = models.CharField(max_length=9, null=True)
    effectif_outre_mer = models.CharField(max_length=9, null=True)
    effectif_groupe = models.CharField(max_length=9, null=True)
    effectif_groupe_france = models.CharField(max_length=9, null=True)
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


class Invitation(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoutee_le = models.DateTimeField()
    modifiee_le = models.DateTimeField()
    inviteur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)
    date_acceptation = models.DateTimeField(null=True)


class Habilitation(models.Model):
    impact_id = models.BigIntegerField(primary_key=True)
    ajoutee_le = models.DateTimeField()
    modifiee_le = models.DateTimeField()
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    fonctions = models.CharField(max_length=FONCTIONS_MAX_LENGTH, null=True)
    confirmee_le = models.DateTimeField(null=True)
    invitation = models.ForeignKey(Invitation, on_delete=models.SET_NULL, null=True)


class Reglementation(models.Model):
    STATUT_A_ACTUALISER = "A ACTUALISER"
    STATUT_EN_COURS = "EN COURS"
    STATUT_A_JOUR = "A JOUR"
    STATUT_CHOICES = [
        (STATUT_A_ACTUALISER, ""),
        (STATUT_EN_COURS, ""),
        (STATUT_A_JOUR, ""),
    ]
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    est_soumise = models.BooleanField(null=True)
    statut = models.CharField(choices=STATUT_CHOICES, max_length=15, null=True)

    class Meta:
        abstract = True


class BDESE(Reglementation):
    pass


class IndexEgaPro(Reglementation):
    pass


class BGES(Reglementation):
    pass


class VSME(Reglementation):
    cree_le = models.DateTimeField()
    modifie_le = models.DateTimeField()
    nb_indicateurs_completes = models.IntegerField(default=0)
    progression = models.IntegerField(default=0)
    progression_B1 = models.IntegerField(default=0)
    progression_B2 = models.IntegerField(default=0)
    progression_B3 = models.IntegerField(default=0)
    progression_B4 = models.IntegerField(default=0)
    progression_B5 = models.IntegerField(default=0)
    progression_B6 = models.IntegerField(default=0)
    progression_B7 = models.IntegerField(default=0)
    progression_B8 = models.IntegerField(default=0)
    progression_B9 = models.IntegerField(default=0)
    progression_B10 = models.IntegerField(default=0)
    progression_B11 = models.IntegerField(default=0)
    progression_C1 = models.IntegerField(default=0)
    progression_C2 = models.IntegerField(default=0)
    progression_C3 = models.IntegerField(default=0)
    progression_C4 = models.IntegerField(default=0)
    progression_C5 = models.IntegerField(default=0)
    progression_C6 = models.IntegerField(default=0)
    progression_C7 = models.IntegerField(default=0)
    progression_C8 = models.IntegerField(default=0)
    progression_C9 = models.IntegerField(default=0)


class Stats(models.Model):
    date = models.DateField(unique=True)
    reglementations_a_jour = models.IntegerField()
    reglementations_statut_connu = models.IntegerField()


class CSRD(Reglementation):
    etape_validee = models.TextField(null=True)
    nb_documents_ia = models.IntegerField(default=0)
    nb_iro_selectionnes = models.IntegerField(default=0)
    lien_rapport = models.BooleanField(default=False)


# Tables temporaires / de travail


class TempTable(TimestampedModel):
    siren = models.CharField(max_length=9, verbose_name="numéro SIREN")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["siren"], name="siren_idx"),
        ]


class TempEgaPro(TempTable):
    annee = models.CharField(max_length=4, verbose_name="année de publication")
    reponse_api = models.JSONField(null=True, verbose_name="réponse de l'API")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["siren", "annee"], name="unique_siren_annee"
            )
        ]


class TempBGES(TempTable):
    dt_publication = models.DateField(verbose_name="date de publication")

    class Meta:
        indexes = [
            models.Index(fields=["dt_publication"], name="dt_publication_idx"),
        ]
