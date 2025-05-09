import random
import string
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from django.db import models

from entreprises.models import Entreprise
from utils.models import TimestampedModel

CODE_MAX_LENGTH = 10


class Invitation(TimestampedModel):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(
        verbose_name="Adresse e-mail",
        max_length=255,
    )
    code = models.CharField(
        verbose_name="Code de validation",
        max_length=CODE_MAX_LENGTH,
    )
    role = models.CharField(
        verbose_name="Role (droits)",
        max_length=20,
    )

    @property
    def date_expiration(self):
        return self.created_at + timedelta(seconds=settings.INVITATION_MAX_AGE)

    @property
    def est_expiree(self):
        return self.created_at + timedelta(
            seconds=settings.INVITATION_MAX_AGE
        ) <= datetime.now(tz=timezone.utc)


def cree_code_invitation():
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for i in range(CODE_MAX_LENGTH))
