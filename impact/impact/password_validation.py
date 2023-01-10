import string

from django.core.exceptions import ValidationError


class CompositionPasswordValidator:
    SPECIAL_CHARS = string.punctuation

    HELP_MSG = "Le mot de passe doit contenir au moins une minuscule, une majuscule, un chiffre et un caractère spécial"

    def validate(self, password, user=None):

        has_lower = any(char.islower() for char in password)
        has_upper = any(char.isupper() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special_char = any(char in self.SPECIAL_CHARS for char in password)

        if not (has_lower and has_upper and has_digit and has_special_char):
            raise ValidationError(self.HELP_MSG, code="password_composition")

    def get_help_text(self):
        return self.HELP_MSG
