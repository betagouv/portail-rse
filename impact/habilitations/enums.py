from django.db import models


class UserRole(models.TextChoices):
    PROPRIETAIRE = "proprietaire", "Propriétaire"
    EDITEUR = "editeur", "Éditeur"
    LECTEUR = "lecteur", "Lecteur"
