from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from django.db import models

from entreprises.models import Entreprise
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
    )
    inviteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    date_acceptation = models.DateTimeField(null=True)

    @property
    def date_expiration(self):
        return self.created_at + timedelta(seconds=settings.INVITATION_MAX_AGE)

    @property
    def est_expiree(self):
        return self.date_expiration <= datetime.now(tz=timezone.utc)
