from entreprises.models import Entreprise


def current_entreprise(request):
    if siren := request.session.get("entreprise"):
        entreprise = Entreprise.objects.get(siren=siren)
    elif request.user.is_authenticated and (
        entreprises := request.user.entreprise_set.all()
    ):
        entreprise = entreprises[0]
    else:
        entreprise = None
    return {"current_entreprise": entreprise}
