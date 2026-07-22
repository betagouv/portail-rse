import pytest

from habilitations.enums import UserRole


@pytest.mark.parametrize(
    "role, roles, expected",
    [
        (UserRole.PROPRIETAIRE, [UserRole.PROPRIETAIRE], True),
        (UserRole.PROPRIETAIRE, [UserRole.CONTRIBUTEUR], True),
        (UserRole.PROPRIETAIRE, [UserRole.LECTEUR], True),
        (UserRole.CONTRIBUTEUR, [UserRole.PROPRIETAIRE], False),
        (UserRole.CONTRIBUTEUR, [UserRole.CONTRIBUTEUR], True),
        (UserRole.CONTRIBUTEUR, [UserRole.LECTEUR], True),
        (UserRole.LECTEUR, [UserRole.PROPRIETAIRE], False),
        (UserRole.LECTEUR, [UserRole.CONTRIBUTEUR], False),
        (UserRole.LECTEUR, [UserRole.LECTEUR], True),
        (UserRole.PROPRIETAIRE, [UserRole.CONTRIBUTEUR, UserRole.LECTEUR], True),
        (UserRole.CONTRIBUTEUR, [UserRole.PROPRIETAIRE, UserRole.LECTEUR], True),
        (UserRole.LECTEUR, [UserRole.LECTEUR], True),
    ],
)
def test_autorise(role, roles, expected):
    assert UserRole.autorise(role, *roles) == expected
