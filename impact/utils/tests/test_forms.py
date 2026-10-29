import pytest
from django.core.exceptions import ValidationError

from utils.forms import SafeEmailField


def test_safe_email_field_accepte_un_email_valide():
    assert SafeEmailField().clean("alice@domaine.test") == "alice@domaine.test"


@pytest.mark.parametrize(
    "email",
    [
        '"<script>alert(1)</script>"@domaine.test',
        '"<svg/onload=alert(1)>"@domaine.test',
    ],
)
def test_safe_email_field_refuse_les_caracteres_html(email):
    with pytest.raises(ValidationError) as erreur:
        SafeEmailField().clean(email)

    assert erreur.value.messages == ["Les caractères < et > ne sont pas autorisés."]
