from django.db import models


class BDESE(models.Model):
    year = models.IntegerField()
    effectif_total = models.IntegerField(
        help_text="Effectif total au 31 décembre",
    )
    effectif_permanent = models.IntegerField()
    effectif_cdd = models.IntegerField(
        "Effectif CDD",
        help_text="Nombre de salariés titulaires d’un contrat de travail à durée déterminée au 31 décembre",
    )
    effectif_mensuel_moyen = models.IntegerField(
        help_text="Effectif mensuel moyen de l'année considérée"
    )
