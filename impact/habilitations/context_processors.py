from .enums import UserRole


def habilitation(request):
    ctx = {}
    siren_courant = request.session.get("entreprise")

    if not siren_courant:
        return ctx

    # ajoute l'habilitation de l'utilisateur pour l'entreprise courante
    # au context sous une forme simplifiée
    for h in request.habilitations:
        if h.entreprise.siren == siren_courant:
            ctx |= {"role_utilisateur": h.role}
            for role in UserRole.values:
                ctx |= {f"est_{role}": UserRole(h.role) >= UserRole(role)}

    return ctx
