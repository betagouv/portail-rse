import json
import os
from uuid import uuid4

import django.db.models as models
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import MinValueValidator
from django.db import transaction
from django.db.models import F
from django.db.models import IntegerField
from django.db.models.query import Cast

from ..enums import EnjeuNormalise
from ..enums import ENJEUX_NORMALISES
from ..enums import ESRS
from utils.models import TimestampedModel


class RapportCSRDQuerySet(models.QuerySet):
    def annee(self, annee: int):
        return self.filter(annee=annee)

    def publies(self):
        return self.exclude(lien_rapport="")


class RapportCSRD(TimestampedModel):
    entreprise = models.ForeignKey(
        "entreprises.Entreprise",
        on_delete=models.CASCADE,
        related_name="rapports_csrd",
    )
    proprietaire = models.ForeignKey(
        "users.User",
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="propriétaire rapport CSRD personnel",
    )  # à supprimer une fois les documents personnels supprimés de la bdd
    annee = models.PositiveIntegerField(
        verbose_name="année du rapport CSRD", validators=[MinValueValidator(2024)]
    )
    description = models.TextField(
        verbose_name="description du rapport CSRD", blank=True
    )
    etape_validee = models.TextField(
        verbose_name="étape validée du rapport CSRD", null=True
    )
    lien_rapport = models.URLField(
        verbose_name="lien du rapport CSRD publié", blank=True
    )
    bloque = models.BooleanField(
        verbose_name="rapport bloqué après publication", default=False
    )

    objects = RapportCSRDQuerySet.as_manager()

    class Meta:
        verbose_name = "rapport CSRD"
        unique_together = [
            ["annee", "entreprise", "proprietaire"]
        ]  # à supprimer une fois les documents personnels supprimés de la bdd
        indexes = [models.Index(fields=["annee"])]

    def __str__(self):
        return f"CSRD {self.annee} - {self.entreprise}"

    def _init_enjeux(self):
        # ajoute les enjeux "réglementés" lors de la création de l'instance
        if self.pk and self.enjeux.filter(modifiable=False).count() >= len(
            ENJEUX_NORMALISES
        ):
            # uniquement pour la création initiale de l'objet
            # on vérifie également que les enjeux normalisés soient créés
            return

        # on ajoute les enjeux normalisés des ESRD
        tmp_enjeux = []

        def _add_enjeux(enjeux: list[EnjeuNormalise], parent=None):
            for enjeu in enjeux:
                ne = Enjeu(
                    esrs=enjeu.esrs,
                    nom=enjeu.nom,
                    description=enjeu.description,
                    parent=parent,
                    modifiable=False,
                    selection=True,
                )
                tmp_enjeux.append(ne)

                if enjeu.children:
                    _add_enjeux(enjeu.children, ne)

        _add_enjeux(ENJEUX_NORMALISES)

        return tmp_enjeux

    def clean(self):
        # à supprimer une fois les documents personnels supprimés de la bdd
        # à remplacer par une contrainte d'unicité sur l'année et l'entreprise

        # La vérification du rapport officiel pourrait être faite par une contrainte (complexe)
        # en base de données, mais le fait d'utiliser une validation métier vérifiable
        # à tout moment est plus simple et plus lisible.
        rapport_officiel = RapportCSRD.objects.filter(
            proprietaire=None, entreprise=self.entreprise, annee=self.annee
        )

        # éviter la duplication avec le rapport officiel existant
        if not self.pk and not self.proprietaire and rapport_officiel.exists():
            raise ValidationError(
                "Il existe déjà un rapport CSRD officiel pour cette entreprise"
            )

        # éviter de transformer un rapport personnel en rapport principal
        if self.pk and self.proprietaire and rapport_officiel.exists():
            if rapport_officiel.first().pk == self.pk:
                raise ValidationError(
                    "Impossible de modifier le rapport CSRD officiel en rapport personnel"
                )

    def save(self, *args, **kwargs):
        # on vérifie si les enjeux réglementaires doivent être ajoutés
        # (premier enregistrement de l 'objet)
        enjeux = self._init_enjeux()

        # on vérifie systématiquement les contraintes métiers avant la sauvegarde
        self.clean()

        # on vérifie si le rapport est actuellement bloqué, auquel cas seuls l'URL de publication
        # et la date de modification sont mis à jour
        kwargs |= (
            {"update_fields": ["lien_rapport", "updated_at", "bloque"]}
            if self.bloque
            else {}
        )

        super().save(*args, **kwargs)

        if self.bloque:
            # plus d'autres modifications possibles si le rapport est bloqué
            return

        if enjeux:
            # Cette partie gènère un N+1 :
            # un `bulk_create` aurait été possible si les enjeux n'avait pas de relation parent-enfant.
            # L'enjeu parent peut ne pas être défini lors de la création de l'enjeu enfant,
            # ce que Django refusera lors de l'insertion (parent pk=None).
            # On pourrait imaginer sauvegarder les parents dans un premier temps, mais l'affichage
            # est en partie basé sur l'ordre naturel d'insertion des enjeux.
            # C'est sans importance, juste un peu plus long à traiter au niveau DB.
            with transaction.atomic():
                self.enjeux.add(*enjeux, bulk=False)

    def nombre_enjeux_selectionnes_par_esrs(self):
        # Retourne un dictionnaire de tuples contenant le nombre d'enjeux sélectionnés par ESRS pour ce rapport
        # par ex.: {"ESRS_E1": 2, "ESRS_E4": 5, ...}
        # note : les ESRS sans enjeux selectionnés ne sont pas dans la liste
        return dict(
            self.enjeux.filter(selection=True)
            .values("esrs")
            .annotate(cnt=models.Count("esrs"))
            .values_list("esrs", "cnt")
        )

    def nombre_enjeux_par_esrs(self):
        # Retourne un dictionnaire de tuples contenant le nombre total d'enjeux par ESRS pour ce rapport
        # par ex.: {"ESRS_E1": 2, "ESRS_E4": 5, ...}
        # note : les ESRS sans enjeux selectionnés ne sont pas dans la liste
        return dict(
            self.enjeux.all()
            .values("esrs")
            .annotate(cnt=models.Count("esrs"))
            .values_list("esrs", "cnt")
        )

    def nombre_enjeux_selectionnes(self):
        return self.enjeux.filter(selection=True).count()

    def nombre_enjeux_non_selectionnes(self):
        return self.enjeux.filter(selection=False).count()

    def enjeux_par_esrs(self, esrs):
        qs = self.enjeux.prefetch_related("enfants")
        qs = qs.filter(esrs=esrs) if esrs else qs.none()
        # l'ordre d'affichage (par pk) est inversé selon que l'enjeu est modifiable ou pas
        qs = qs.annotate(
            ord=Cast("modifiable", output_field=IntegerField()) * F("pk")
        ).order_by("-ord", "pk")
        return qs

    @property
    def documents_analyses(self):
        return self.documents.filter(etat__exact="success")

    @property
    def documents_non_analyses(self):
        return self.documents.filter(etat__isnull=True)

    @property
    def est_termine(self):
        # on peut considérer un rapport CSRD comme terminé une fois son rapport publié
        return bool(self.lien_rapport) and self.bloque


class EnjeuQuerySet(models.QuerySet):
    def selectionnes(self):
        return self.filter(selection=True)

    def non_selectionnes(self):
        return self.filter(selection=False)

    def modifiables(self):
        return self.filter(modifiable=True)

    def materiels(self):
        return self.selectionnes().filter(materiel=True)

    def non_materiels(self):
        return self.selectionnes().filter(materiel=False)

    def analyses(self):
        return self.selectionnes().filter(materiel__isnull=False)

    def non_analyses(self):
        return self.selectionnes().filter(materiel__isnull=True)

    def environnement(self):
        return self.filter(esrs__startswith="ESRS_E")

    def social(self):
        return self.filter(esrs__startswith="ESRS_S")

    def gouvernance(self):
        return self.filter(esrs__startswith="ESRS_G")


class Enjeu(TimestampedModel):
    rapport_csrd = models.ForeignKey(
        "RapportCSRD", on_delete=models.CASCADE, related_name="enjeux"
    )
    parent = models.ForeignKey(
        "Enjeu",
        null=True,
        on_delete=models.CASCADE,
        verbose_name="enjeu parent",
        related_name="enfants",
    )
    esrs = models.TextField(choices=ESRS.choices, verbose_name="ESRS rattaché")

    nom = models.TextField(verbose_name="nom de l'enjeu")
    description = models.TextField(verbose_name="description de l'enjeu", blank=True)

    # les enjeux réglementés ne sont pas modifiables
    modifiable = models.BooleanField(
        verbose_name="enjeu modifiable par l'utilisateur", default=True
    )
    selection = models.BooleanField(verbose_name="selectionné", default=False)

    # l'utilisateur doit explicitement selectionner l'enjeu comme enjeu matériel (nullable)
    materiel = models.BooleanField(
        verbose_name="sélectionné comme enjeu matériel", null=True
    )

    class Meta:
        verbose_name = "enjeu ESRS"
        unique_together = [["rapport_csrd", "nom", "esrs"]]
        indexes = [models.Index(fields=["esrs"])]
        ordering = ["rapport_csrd", "id"]

    objects = EnjeuQuerySet.as_manager()

    def __repr__(self):
        return f"{self.esrs} - {self.nom}"

    def __str__(self):
        return self.nom


def select_storage():
    # Utiliser un autre storage que celui par défaut ne permet pas de le modifier dans les tests
    # https://code.djangoproject.com/ticket/36269
    return default_storage


def upload_path(instance, filename):
    return f"analyse_ia/{str(uuid4())}.pdf"


class DocumentAnalyseIA(TimestampedModel):
    rapport_csrd = models.ForeignKey(
        "RapportCSRD", on_delete=models.CASCADE, related_name="documents"
    )
    fichier = models.FileField(storage=select_storage, upload_to=upload_path)
    nom = models.CharField(max_length=255, verbose_name="nom d'origine")
    resultat_json = models.JSONField(
        null=True, verbose_name="résultat de l'analyse IA au format JSON"
    )
    etat = models.CharField(
        max_length=144,
        null=True,
        verbose_name="dernier état connu du traitement d'analyse IA envoyé par le serveur IA",
    )
    message = models.CharField(
        max_length=144,
        null=True,
        verbose_name="éventuel message précisant l'état envoyé par le serveur IA",
    )

    class Meta:
        verbose_name = "document analyse IA"
        verbose_name_plural = "documents analyse IA"

    def __str__(self):
        return f"DocumentAnalyseIA {self.id} - {self.nom}"

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
