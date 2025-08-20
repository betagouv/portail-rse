from django.conf import settings


def cache_partiellement_un_email(email):
    if email == settings.SUPPORT_EMAIL:
        return email
    nom, domaine = email.split("@")
    etoiles = "*" * (len(nom) - 2)
    nom_cache = cache_partiellement_un_mot(nom)
    return f"{nom_cache}@{domaine}"


def cache_partiellement_un_mot(mot):
    etoiles = "*" * (len(mot) - 2)
    return f"{mot[0]}{etoiles}{mot[-1]}"
