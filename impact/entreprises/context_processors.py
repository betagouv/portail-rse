from entreprises.views import get_current_entreprise


def current_entreprise(request):
    return {"current_entreprise": get_current_entreprise(request)}
