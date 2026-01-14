from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from django.db import models

from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from users.models import User
from utils.models import TimestampedModel


class Invitation(TimestampedModel):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(
        verbose_name="Adresse e-mail",
        max_length=255,
    )
    role = models.CharField(
        verbose_name="Role (droits)",
        max_length=20,
        choices=UserRole.choices,
    )
    inviteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    date_acceptation = models.DateTimeField(null=True)
    est_invitation_proprietaire_tiers = models.BooleanField(
        default=False,
        verbose_name="Invitation propriétaire pour un tiers",
        help_text="Invitation créée par un conseiller RSE pour un futur propriétaire",
    )

    @property
    def date_expiration(self):
        return self.created_at + timedelta(seconds=settings.INVITATION_MAX_AGE)

    @property
    def est_expiree(self):
        return self.date_expiration <= datetime.now(tz=timezone.utc)

    def accepter(self, utilisateur, fonctions=None):
        Habilitation.ajouter(
            self.entreprise,
            utilisateur,
            role=self.role,
            fonctions=fonctions,
            invitation=self,
        )

        self.date_acceptation = datetime.now(timezone.utc)
        self.save()
        return self
