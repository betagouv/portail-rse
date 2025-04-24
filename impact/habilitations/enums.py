from typing import override

from django.db import models


class UserRole(models.TextChoices):
    """
    Gestion simple (simpliste?) des rôles d'utilisation:
     - un PROPRIETAIRE possède les droits de LECTEUR et EDITEUR
     - un EDITEUR a aussi les droits de LECTEUR
     - un LECTEUR est moins que rien
    Pourra être remanié au besoin si des besoins plus fins sont nécessaires,
    le principal est de *centraliser* l'évaluation des droits.
    """

    PROPRIETAIRE = "proprietaire", "Propriétaire"
    EDITEUR = "editeur", "Éditeur"
    LECTEUR = "lecteur", "Lecteur"

    @override
    def __eq__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self.value == other.value

    # Note :
    # pour une raison que je ne m'explique pas (encore ?) `@functools.total_ordering` semble ne *pas* fonctionner ici :
    # - l'implementation automatique de `__lt__` ne donne pas les bons résultats dans les tests (?!)
    # - `__gt__` ne semble pas mieux fonctionner
    # Probablement à cause du contexte Django, mais pourquoi ? Sinon c'est un bug en 3.12.x mais j'en doute.
    # En attendant, je réimplémente toutes les méthodes de comparaison manuellement : les tests passent (!)

    def __lt__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._sort_order_ > other._sort_order_

    def __gt__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._sort_order_ < other._sort_order_

    def __le__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._sort_order_ >= other._sort_order_

    def __ge__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._sort_order_ <= other._sort_order_

    @classmethod
    def autorise(cls, role_utilisateur: "UserRole", *roles: "UserRole") -> bool:
        # vérifie si le rôle utilisateur est supérieur ou égal à un des rôles donnés
        if not isinstance(role_utilisateur, UserRole) or not all(
            isinstance(r, UserRole) for r in roles
        ):
            return False

        return any(role_utilisateur >= r for r in roles)
