from invitations.models import CODE_MAX_LENGTH
from invitations.models import cree_code_invitation


def test_cree_code_invitation():
    assert len(cree_code_invitation()) == CODE_MAX_LENGTH
    assert cree_code_invitation() != cree_code_invitation()
