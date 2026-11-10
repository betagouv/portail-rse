from django.db import models

from utils.models import TimestampedModel


class PreremplissageLee(TimestampedModel):
    rapport_vsme = models.ForeignKey(
        "vsme.RapportVSME",
        on_delete=models.CASCADE,
        related_name="preremplissages_lee",
    )
    schema_id = models.CharField(max_length=42)
    data = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rapport_vsme", "schema_id"],
                name="unique_preremplissage_lee_par_rapport",
            ),
        ]
