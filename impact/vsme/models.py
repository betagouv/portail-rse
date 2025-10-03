from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from utils.models import TimestampedModel


class RapportVSME(TimestampedModel):
    entreprise = models.ForeignKey(
        "entreprises.Entreprise",
        on_delete=models.CASCADE,
        related_name="rapports_vsme",
    )
    annee = models.PositiveIntegerField(
        verbose_name="année du rapport VSME",
    )

    class Meta:
        verbose_name = "rapport VSME"
        verbose_name_plural = "rapports VSME"
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "annee"],
                name="unique_rapport_annuel",
            ),
        ]
        indexes = [models.Index(fields=["annee"])]

    def indicateurs_actifs(self, exigence_de_publication):
        exigence_de_publication_schema = exigence_de_publication.load_json_schema()
        indicateurs_actifs = [
            ind
            for ind in exigence_de_publication_schema
            if self.indicateur_est_actif(ind)
        ]
        return indicateurs_actifs

    def indicateur_est_actif(self, indicateur_schema_id):
        if indicateur_schema_id == "B1-24-d":  # indicateur liste filiales
            indicateur_type_de_perimetre = "B1-24-c"
            try:
                base_consolidee = (
                    self.indicateurs.get(schema_id=indicateur_type_de_perimetre).data[
                        "type_perimetre"
                    ]
                    == "consolidee"
                )
            except ObjectDoesNotExist:
                base_consolidee = False
            return base_consolidee
        else:
            return True

    def indicateurs_completes(self, exigence_de_publication):
        return self.indicateurs.filter(
            schema_id__startswith=exigence_de_publication.code
        ).values_list("schema_id", flat=True)

    def progression_par_exigence(self, exigence_de_publication):
        complet = self.indicateurs_completes(exigence_de_publication).count()
        total = len(self.indicateurs_actifs(exigence_de_publication))
        pourcent = (complet / total) * 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}

    def progression_par_categorie(self, categorie):
        complet, total = 0, 0
        for exigence_de_publication in categorie.exigences_de_publication():
            if exigence_de_publication.remplissable:
                progression_exigence = self.progression_par_exigence(
                    exigence_de_publication
                )
                complet += progression_exigence["complet"]
                total += progression_exigence["total"]
        pourcent = (complet / total) * 100
        return {"total": total, "complet": complet, "pourcent": int(pourcent)}


class Indicateur(TimestampedModel):
    rapport_vsme = models.ForeignKey(
        "RapportVSME",
        on_delete=models.CASCADE,  # models.SET_NULL si un indicateur peut se trouver dans plusieurs réglementations à terme ?
        # blank=True,
        # null=True,
        # Si d'autres réglementations peuvent avoir des indicateurs
        related_name="indicateurs",
    )
    schema_id = models.CharField(
        max_length=42, verbose_name="id du schéma descriptif de l'indicateur"
    )  # type B1-24-a-i-P1
    schema_version = models.PositiveIntegerField(
        verbose_name="numéro de version du schéma descriptif de l'indicateur", default=1
    )
    data = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name="donnée brute saisie par l'utilisateur",
    )
    # est_complete ?

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rapport_vsme", "schema_id"],
                name="unique_indicateur_par_rapport",
            ),
        ]
        indexes = [models.Index(fields=["schema_id"])]
