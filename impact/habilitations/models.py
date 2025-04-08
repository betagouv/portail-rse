import warnings
from datetime import datetime
from datetime import timezone

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .enums import UserRole
from entreprises.models import Entreprise
from reglementations.models import get_all_personal_bdese
from reglementations.models import has_official_bdese
from utils.models import TimestampedModel

FONCTIONS_MIN_LENGTH = 3
FONCTIONS_MAX_LENGTH = 250


class HabilitationManager(models.Manager):
    def parEntreprise(self, entreprise):
        return self.filter(entreprise=entreprise)

    def parUtilisateur(self, utilisateur):
        return self.filter(user=utilisateur)

    def parRole(self, role):
        return self.filter(role=role)


class Habilitation(TimestampedModel):
    """
    L'habilitation permet de rattacher l'utilisateur, l'entreprise, et son rôle.

    Note : la plupart des fonctionnalité relatives à la confirmation seront dépréciées lors
    du remaniement des parties CSRD et BDESE.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="utilisateur",
    )
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PROPRIETAIRE,
        verbose_name="rôle",
    )

    # TODO: isoler les utilisations
    fonctions = models.CharField(
        verbose_name="fonction(s) dans la société",
        max_length=FONCTIONS_MAX_LENGTH,
        null=True,
        blank=True,
    )

    # note: au 09.04.2025, seules 32 habilitations sont confirmées (0.35%)
    # TODO : éventuellement à déprécier après modifications sur la CSRD et BDESE
    confirmed_at = models.DateTimeField(
        verbose_name="confirmée le",
        null=True,
    )

    objects = HabilitationManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "entreprise", "user"],
                name="unique_role_entreprise_user",
            )
        ]

    def __str__(self):
        return f"Habilitation : {self.entreprise}, {self.user}, {self.role}"

    def confirm(self):
        warnings.warn("fonctionnalité dépréciée")
        self.confirmed_at = datetime.now(timezone.utc)
        if not has_official_bdese(self.entreprise):
            for bdese in get_all_personal_bdese(self.entreprise, self.user):
                bdese.officialize()

    def unconfirm(self):
        warnings.warn("fonctionnalité dépréciée")
        self.confirmed_at = None

    @property
    def is_confirmed(self):
        warnings.warn("fonctionnalité dépréciée")
        return bool(self.confirmed_at)


def attach_user_to_entreprise(user, entreprise, fonctions):
    warnings.warn("fonctionnalité dépréciée")
    return Habilitation.objects.create(
        user=user,
        entreprise=entreprise,
        fonctions=fonctions,
    )


def detach_user_from_entreprise(user, entreprise):
    warnings.warn("fonctionnalité dépréciée")
    get_habilitation(user, entreprise).delete()


def get_habilitation(user, entreprise):
    warnings.warn("fonctionnalité dépréciée")
    return Habilitation.objects.get(
        user=user,
        entreprise=entreprise,
    )


def is_user_attached_to_entreprise(user, entreprise):
    warnings.warn("fonctionnalité dépréciée")
    try:
        get_habilitation(user, entreprise)
        return True
    except (ObjectDoesNotExist, TypeError):
        return False


def is_user_habilited_on_entreprise(user, entreprise):
    warnings.warn("fonctionnalité dépréciée")
    return (
        is_user_attached_to_entreprise(user, entreprise)
        and get_habilitation(user, entreprise).is_confirmed
    )
