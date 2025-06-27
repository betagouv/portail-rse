import logging
import pprint
import uuid

import django.db.models as models

# Pour les indexes BRIN
# from django.contrib.postgres.indexes import BrinIndex


class EventLog(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="identifiant"
    )

    created_at = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="date de création"
    )

    level = models.SmallIntegerField(
        null=False,
        blank=True,
        verbose_name="niveau de log",
        editable=False,
        choices=logging._levelToName.items(),
    )

    msg = models.TextField(null=False, blank=True, verbose_name="message")

    payload = models.JSONField(
        default=dict,
        null=False,
        blank=True,
        verbose_name="contenu supplémentaire (JSON)",
    )

    # note :
    # pour l'instant, pas d'implémentation de recherche sur le contenu du message du log.
    # le système actuel se veut simple et ne nécessitera pas forcément une recherche "fulltext".
    # si le cas se présente :
    # - ajouter un champ de type `SearchVectorField` par ex.
    # - indexer le champ `msg` (GIN)

    class Meta:
        verbose_name = "historique des évenements"
        verbose_name_plural = "historique des évenements"

        # Quelque chose comme :
        # indexes = (
        #     BrinIndex(
        #         fields=("created_at",),
        #         name="idx_%(app_label)s_%(class)s_created_at",
        #         autosummarize=True,
        #     ),
        #     models.Index(fields=("level",)),
        # )
        # serait plus optimisé pour effectuer des recherches par encadrement de dates
        # mais les indexes BRIN ne sont disponibles que sur postgres (et la CI tourne sur Sqlite)
        # En attendant, on utilisera des B-Tree

        # FIXME : changer la CI qui tourne sur Sqlite et les environnements de dev

        indexes = (
            models.Index(fields=("level",)),
            models.Index(
                fields=("created_at",), name="idx_%(app_label)s_%(class)s_created_at"
            ),
        )

    def __repr__(self):
        return pprint.pformat(
            {
                "_id": str(self.pk),
                "_createdAt": str(self.created_at),
                "_msg": self.msg,
                "_level": self.level,
            }
            | self.payload
        )

    def __str__(self):
        return f"{str(self.pk)} - {self.level_name}"

    @property
    def level_name(self):
        return logging._levelToName[self.level]
