from utils.tokens import check_token
from utils.tokens import make_token


def test_email_token(alice, bob):
    salt = "KEYSALT"
    assert make_token(alice, salt) != make_token(bob, salt)

    token = make_token(alice, salt)
    assert check_token(alice, salt, token)
    assert not check_token(alice, "salt", token)
    assert not check_token(alice, salt, "invalid-token")
    assert not check_token(bob, salt, token)
