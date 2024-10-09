import django.db.models as models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
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

    def officiels(self):
        return self.filter(proprietaire=None)

    def personnels(self):
        return self.exclude(proprietaire=None)


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
    )
    annee = models.PositiveIntegerField(
        verbose_name="année du rapport CSRD", validators=[MinValueValidator(2024)]
    )
    description = models.TextField(
        verbose_name="description du rapport CSRD", blank=True
    )

    objects = RapportCSRDQuerySet.as_manager()

    class Meta:
        verbose_name = "rapport CSRD"
        unique_together = [["annee", "entreprise", "proprietaire"]]
        indexes = [models.Index(fields=["annee"])]

    def __str__(self):
        return f"CRSD {self.annee} - {self.entreprise}"

    def _init_enjeux(self):
        # ajoute les enjeux "réglementés" lors de la création de l'instance
        if self.pk:
            # uniquement pour la création initiale de l'objet
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
                )
                tmp_enjeux.append(ne)

                if enjeu.children:
                    _add_enjeux(enjeu.children, ne)

        _add_enjeux(ENJEUX_NORMALISES)

        return tmp_enjeux

    def clean(self):
        # La vérification du rapport officiel pourrait être faite par une contrainte (complexe)
        # en base de données, mais le fait d'utiliser une validation métier vérifiable
        # à tout moment est plus simple et plus lisible.
        already_exists = RapportCSRD.objects.filter(
            proprietaire=None, entreprise=self.entreprise
        ).exists()

        if not self.proprietaire and already_exists:
            raise ValidationError(
                "Il existe déjà un rapport CSRD officiel pour cette entreprise"
            )

        if self.pk and already_exists and self.proprietaire:
            raise ValidationError(
                "Impossible de modifier le rapport CSRD officiel en rapport personnel"
            )

        ...

    def save(self, *args, **kwargs):
        enjeux = self._init_enjeux()

        # on vérifie systématiquement les contraintes métiers avant la sauvegarde
        self.clean()
        super().save(*args, **kwargs)

        if enjeux:
            self.enjeux.add(*enjeux, bulk=False)

    def est_officiel(self):
        # le rapport CSRD n'a un propriétaire que si c'est un rapport personnel
        return self.pk and not self.proprietaire

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

    def modifiable_par(self, utilisateur: "users.User") -> bool:
        # Vérifie si le rapport CSRD courant est modifiable par un utilisateur donné.
        # tip : un utilisateur anonyme n'a pas d'ID
        return (
            utilisateur
            and utilisateur.id
            and (
                # l'utilisateur est le propriétaire du rapport (personnel)
                self.proprietaire == utilisateur
                # l'utilisateur à une habilitation confirmée pour cette entreprise
                or utilisateur.habilitation_set.exclude(confirmed_at=None)
                .filter(entreprise=self.entreprise)
                .exists()
            )
        )

    def enjeux_par_esrs(self, esrs):
        qs = self.enjeux.prefetch_related("enfants")
        qs = qs.filter(esrs=esrs) if esrs else qs.none()
        # l'ordre d'affichage (par pk) est inversé selon que l'enjeu est modifiable ou pas
        qs = qs.annotate(
            ord=Cast("modifiable", output_field=IntegerField()) * F("pk")
        ).order_by("-ord", "pk")
        return qs


class EnjeuQuerySet(models.QuerySet):
    def selectionnes(self):
        return self.filter(selection=True)

    def modifiables(self):
        return self.filter(modifiable=True)


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
    modifiable = models.BooleanField(
        verbose_name="enjeu modifiable par l'utilisateur", default=True
    )
    selection = models.BooleanField(verbose_name="selectionné", default=False)

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


def rapport_csrd_officiel(entreprise):  # ajouter l'année ?
    return RapportCSRD.objects.filter(entreprise=entreprise).first()


def rapport_csrd_personnel(entreprise, proprietaire):  # ajouter l'année ?
    return RapportCSRD.objects.filter(
        entreprise=entreprise, proprietaire=proprietaire
    ).first()
