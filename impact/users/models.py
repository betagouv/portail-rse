from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

from utils.models import TimestampedModel


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
    email = models.EmailField(
        verbose_name="Email",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    acceptation_cgu = models.BooleanField(default=False)
    reception_actualites = models.BooleanField(default=False)
    prenom = models.CharField(max_length=SURNAME_MAX_LENGTH, default="")
    nom = models.CharField(max_length=NAME_MAX_LENGTH, default="")

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
