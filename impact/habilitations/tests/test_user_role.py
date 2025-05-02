import pytest

from habilitations.enums import UserRole


@pytest.mark.parametrize(
    "role, roles, expected",
    [
        (UserRole.PROPRIETAIRE, [UserRole.PROPRIETAIRE], True),
        (UserRole.PROPRIETAIRE, [UserRole.EDITEUR], True),
        (UserRole.PROPRIETAIRE, [UserRole.LECTEUR], True),
        (UserRole.EDITEUR, [UserRole.PROPRIETAIRE], False),
        (UserRole.EDITEUR, [UserRole.EDITEUR], True),
        (UserRole.EDITEUR, [UserRole.LECTEUR], True),
        (UserRole.LECTEUR, [UserRole.PROPRIETAIRE], False),
        (UserRole.LECTEUR, [UserRole.EDITEUR], False),
        (UserRole.LECTEUR, [UserRole.LECTEUR], True),
        (UserRole.PROPRIETAIRE, [UserRole.EDITEUR, UserRole.LECTEUR], True),
        (UserRole.EDITEUR, [UserRole.PROPRIETAIRE, UserRole.LECTEUR], True),
    ],
)
def test_autorise(role, roles, expected):
    assert UserRole.autorise(role, *roles) == expected
