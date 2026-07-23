import pytest

from habilitations.enums import UserRole


@pytest.mark.parametrize(
    "role, roles, expected",
    [
        (UserRole.ADMINISTRATEUR, [UserRole.ADMINISTRATEUR], True),
        (UserRole.ADMINISTRATEUR, [UserRole.CONTRIBUTEUR], True),
        (UserRole.ADMINISTRATEUR, [UserRole.LECTEUR], True),
        (UserRole.CONTRIBUTEUR, [UserRole.ADMINISTRATEUR], False),
        (UserRole.CONTRIBUTEUR, [UserRole.CONTRIBUTEUR], True),
        (UserRole.CONTRIBUTEUR, [UserRole.LECTEUR], True),
        (UserRole.LECTEUR, [UserRole.ADMINISTRATEUR], False),
        (UserRole.LECTEUR, [UserRole.CONTRIBUTEUR], False),
        (UserRole.LECTEUR, [UserRole.LECTEUR], True),
        (UserRole.ADMINISTRATEUR, [UserRole.CONTRIBUTEUR, UserRole.LECTEUR], True),
        (UserRole.CONTRIBUTEUR, [UserRole.ADMINISTRATEUR, UserRole.LECTEUR], True),
        (UserRole.LECTEUR, [UserRole.LECTEUR], True),
    ],
)
def test_autorise(role, roles, expected):
    assert UserRole.autorise(role, *roles) == expected
