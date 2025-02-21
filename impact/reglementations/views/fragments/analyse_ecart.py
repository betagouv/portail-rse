from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from reglementations.forms import DocumentAnalyseIAForm


@login_required
@require_http_methods(["POST"])
def ajout_document(request, csrd_id):
    data = {**request.POST}
    data["rapport_csrd"] = csrd_id
    form = DocumentAnalyseIAForm(data=data, files=request.FILES)
    if form.is_valid():
        form.save()
        referer = request.META.get("HTTP_REFERER")
        return redirect(referer)
    else:
        print(form.errors)
