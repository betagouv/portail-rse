from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.db import models

from utils.models import TimestampedModel
from utils.tokens import uidb64


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email,
            password=password,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user


SURNAME_MAX_LENGTH = NAME_MAX_LENGTH = 50


class User(AbstractBaseUser, TimestampedModel):
    class Meta:
        verbose_name = "Utilisateur"

    email = models.EmailField(
        verbose_name="Adresse e-mail",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        verbose_name="Accès à /admin (back-office)",
        default=False,
    )
    acceptation_cgu = models.BooleanField(
        verbose_name="CGU acceptées",
        default=False,
    )
    reception_actualites = models.BooleanField(
        verbose_name="Réception des actualités acceptée",
        default=False,
    )
    prenom = models.CharField(
        verbose_name="Prénom",
        max_length=SURNAME_MAX_LENGTH,
        default="",
    )
    nom = models.CharField(
        max_length=NAME_MAX_LENGTH,
        default="",
    )
    is_email_confirmed = models.BooleanField(
        verbose_name="Adresse e-mail confirmée",
        default=False,
    )

    sub = models.UUIDField(
        verbose_name="identifiant interne ProConnect",
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def entreprises(self):
        return self.entreprise_set.all()

    @property
    def uidb64(self):
        return uidb64(self)

    @property
    def is_superuser(self):
        # FIXME:
        # la gestion des super-utilisateurs et droits pour l'admin doit être revue :
        # - pas d'alias pour ce champ
        # - ajout de PermissionMixin pour le modèle
        return self.is_staff
