from django.db import models


class UserRole(models.TextChoices):
    """
    Gestion simple (simpliste?) des rôles d'utilisation:
     - un PROPRIETAIRE possède les droits de LECTEUR et EDITEUR
     - un EDITEUR a aussi les droits de LECTEUR
     - un LECTEUR est moins que rien
    Pourra être remanié au besoin si des besoins plus fins sont nécessaires,
    le principal est de centraliser l'évaluation des droits.
    """

    PROPRIETAIRE = "proprietaire", "Propriétaire"
    EDITEUR = "editeur", "Éditeur"
    LECTEUR = "lecteur", "Lecteur"

    @classmethod
    def autorise(cls, role, *roles):
        # définition des "poids" : du plus important au plus faible
        poids = [cls.PROPRIETAIRE, cls.EDITEUR, cls.LECTEUR]
        for r in roles:
            if poids.index(role) <= poids.index(r):
                return True
        return False
