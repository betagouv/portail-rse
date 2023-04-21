def get_token(user):
    return user.email


def check_token(user, token):
    return user.email == token
