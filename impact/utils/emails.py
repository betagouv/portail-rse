def cache_partiellement_un_email(email):
    nom, domaine = email.split("@")
    etoiles = "*" * (len(nom) - 2)
    return f"{nom[0]}{etoiles}{nom[-1]}@{domaine}"
