import random
import string

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


def cree_code_invitation():
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for i in range(CODE_MAX_LENGTH))
