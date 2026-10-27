from .enums import UserRole


def habilitation(request):
    ctx = {}
    id_entreprise = request.session.get("entreprise")

    if not id_entreprise:
        return ctx

    # ajoute l'habilitation de l'utilisateur pour l'entreprise courante
    # au context sous une forme simplifiée
    for h in request.habilitations:
        if h.entreprise_id == id_entreprise:
            ctx |= {"role_utilisateur": h.role}
            for role in UserRole.values:
                ctx |= {f"est_{role}": UserRole(h.role) >= UserRole(role)}
            break

    return ctx
