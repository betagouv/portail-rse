import logging
import warnings
from datetime import datetime
from datetime import timezone

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.utils import IntegrityError

from .enums import UserRole
from entreprises.models import Entreprise
from utils.models import TimestampedModel

FONCTIONS_MIN_LENGTH = 3
FONCTIONS_MAX_LENGTH = 250
logger = logging.getLogger(__name__)


class HabilitationError(Exception):
    pass


class HabilitationQueryset(models.QuerySet):
    def parEntreprise(self, entreprise):
        return self.filter(entreprise=entreprise)

    def parUtilisateur(self, utilisateur):
        return self.filter(user=utilisateur)

    def parRole(self, role):
        return self.filter(role=role)

    def pour(self, entreprise, utilisateur):
        return self.get(user=utilisateur, entreprise=entreprise)


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
        validators=[
            MinLengthValidator(FONCTIONS_MIN_LENGTH),
            MaxLengthValidator(FONCTIONS_MAX_LENGTH),
        ],
        null=True,
        blank=True,
    )

    # note: au 09.04.2025, seules 32 habilitations sont confirmées (0.35%)
    # TODO : éventuellement à déprécier après modifications sur la CSRD et BDESE
    confirmed_at = models.DateTimeField(
        verbose_name="confirmée le",
        null=True,
    )

    invitation = models.ForeignKey(
        "invitations.Invitation",
        verbose_name="invitation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = HabilitationQueryset.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "user"],
                name="unique_entreprise_user",
            )
        ]

    def __str__(self):
        return f"Habilitation : {self.entreprise}, {self.user}, {self.role}"

    def __eq__(self, h):
        # pour une utilisation avec `in`
        return (
            isinstance(h, Habilitation)
            and self.entreprise_id == h.entreprise_id
            and self.user_id == h.user_id
            and self.role == h.role
        )

    def __hash__(self):
        # pas de `__eq__` sans `__hash__`
        # `self.pk` inutile à cause de la contrainte d'intégrité
        return hash((self.user_id, self.entreprise_id, self.role))

    # comparaisons des habilitations en fonction des rôles
    # uniquement pour les habilitations d'un même tuple (entreprise,utilisateur)

    def _same_origin(self, other):
        return (
            isinstance(other, Habilitation)
            and self.entreprise == other.entreprise
            and self.user == other.user
        )

    # Les méthodes de comparaison suivantes ne sont valides que pour
    # des habilitations concernant le même utilisateur et la même entreprise.

    def __lt__(self, other):
        if not self._same_origin(other):
            return NotImplemented
        return self.role < other.role

    def __le__(self, other):
        if not self._same_origin(other):
            return NotImplemented
        return self.role <= other.role

    def __gt__(self, other):
        if not self._same_origin(other):
            return NotImplemented
        return self.role > other.role

    def __ge__(self, other):
        if not self._same_origin(other):
            return NotImplemented
        return self.role >= other.role

    @classmethod
    def ajouter(
        cls,
        entreprise,
        utilisateur,
        role=UserRole.PROPRIETAIRE,
        fonctions=None,
        invitation=None,
    ):
        # Un conseiller RSE ne peut pas être propriétaire d'une entreprise
        if utilisateur.is_conseiller_rse and role == UserRole.PROPRIETAIRE:
            raise HabilitationError(
                "Un conseiller RSE ne peut pas être propriétaire d'une entreprise."
            )
        h = cls(user=utilisateur, entreprise=entreprise, role=role)
        if fonctions:
            h.fonctions = fonctions
        if invitation:
            h.invitation = invitation
        try:
            h.save()
            return h
        except IntegrityError:
            logger.warning(
                "Une habilitation existe déjà: entreprise=%s, utilisateur=%s",
                entreprise,
                utilisateur,
            )

    @classmethod
    def retirer(cls, entreprise, utilisateur):
        # on vérifie que l'entreprise disposera d'un propriétaire
        # après le retrait
        habilitations = cls.objects.parEntreprise(entreprise).parRole(
            UserRole.PROPRIETAIRE
        )
        if habilitations.count() == 1:
            h = habilitations.first()
            if h.user == utilisateur:
                raise HabilitationError(
                    "Vous ne pouvez pas quitter cette entreprise car vous en êtes le seul propriétaire. Commencez par ajouter un nouveau propriétaire à l'entreprise avant de la quitter. En cas de problème n'hésitez pas à contacter le support."
                )

        try:
            cls.objects.get(entreprise=entreprise, user=utilisateur).delete()
        except Habilitation.DoesNotExist:
            logger.warning(
                "Il n'y a pas d'habilitation pour: entreprise=%s, utilisateur=%s",
                entreprise,
                utilisateur,
            )
            raise HabilitationError(
                "Aucune habilitation pour cet l'utilisateur dans cette entreprise"
            )

    @classmethod
    def existe(cls, entreprise, utilisateur) -> bool:
        return cls.objects.filter(entreprise=entreprise, user=utilisateur).exists()

    @classmethod
    def pour(cls, entreprise, utilisateur):
        return cls.objects.pour(entreprise, utilisateur)

    @classmethod
    def role_pour(cls, entreprise, utilisateur) -> UserRole:
        return UserRole(cls.pour(entreprise, utilisateur).role)

    # Méthodes dépréciées : confirmation de l'habilitation

    def confirm(self):
        warnings.warn("fonctionnalité dépréciée : confirmation de l'habilitation")
        self.confirmed_at = datetime.now(timezone.utc)

    def unconfirm(self):
        warnings.warn(
            "fonctionnalité dépréciée : annulation de la confirmation de l'habilitation"
        )
        self.confirmed_at = None

    @property
    def is_confirmed(self):
        warnings.warn(
            "fonctionnalité dépréciée : vérification de la confirmation de l'habilitation"
        )
        return bool(self.confirmed_at)


def is_user_habilited_on_entreprise(user, entreprise):
    warnings.warn(
        "fonctionnalité dépréciée : habilitation d'un utilisateur (utiliser `pour` ou `role_pour`)"
    )
    return (
        Habilitation.existe(entreprise, user)
        and Habilitation.pour(entreprise, user).is_confirmed
    )
