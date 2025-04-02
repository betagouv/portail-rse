from django.db import models

class UserRole(models.TextChoices):
    PROPRIETAIRE = 'propriétaire', 'Propriétaire'
    EDITEUR = 'éditeur', 'Éditeur'
    LECTEUR = 'lecteur', 'Lecteur'
