from django.urls import path
from django.views.generic.base import TemplateView

from reglementations import views

app_name = "reglementations"
urlpatterns = [
    path(
        "reglementations/bdese",
        TemplateView.as_view(template_name="reglementations/fiches/bdese.html"),
        name="fiche_bdese",
    ),
    path(
        "reglementations/index-egalite-professionnelle",
        TemplateView.as_view(
            template_name="reglementations/fiches/index-egalite-professionnelle.html",
            extra_context={
                "reglementation": views.index_egapro.IndexEgaproReglementation
            },
        ),
        name="fiche_index_egapro",
    ),
    path(
        "reglementations/dispositif-alerte",
        TemplateView.as_view(
            template_name="reglementations/fiches/dispositif-alerte.html"
        ),
        name="fiche_dispositif_alerte",
    ),
    path(
        "reglementations/bilan-ges",
        TemplateView.as_view(template_name="reglementations/fiches/bilan-ges.html"),
        name="fiche_bilan_ges",
    ),
    path(
        "reglementations/audit-energetique",
        TemplateView.as_view(
            template_name="reglementations/fiches/audit-energetique.html"
        ),
        name="fiche_audit_energetique",
    ),
    path(
        "reglementations/dispositif-anticorruption",
        TemplateView.as_view(
            template_name="reglementations/fiches/dispositif-anticorruption.html"
        ),
        name="fiche_dispositif_anticorruption",
    ),
    path(
        "reglementations/declaration-de-performance-extra-financiere",
        TemplateView.as_view(template_name="reglementations/fiches/dpef.html"),
        name="fiche_dpef",
    ),
    path(
        "reglementations/rapport-durabilite-csrd",
        TemplateView.as_view(
            template_name="reglementations/fiches/csrd.html",
            extra_context={"reglementation": views.csrd.CSRDReglementation},
        ),
        name="fiche_csrd",
    ),
    path(
        "reglementations/plan-vigilance",
        TemplateView.as_view(
            template_name="reglementations/fiches/plan-vigilance.html",
            extra_context={
                "reglementation": views.plan_vigilance.PlanVigilanceReglementation
            },
        ),
        name="fiche_plan_vigilance",
    ),
    path(
        "tableau-de-bord/<str:siren>",
        views.tableau_de_bord,
        name="tableau_de_bord",
    ),
    path(
        "bdese/<str:siren>/<int:annee>/<int:step>",
        views.bdese.bdese_step,
        name="bdese_step",
    ),
    path("bdese/<str:siren>/<int:annee>/pdf", views.bdese.bdese_pdf, name="bdese_pdf"),
    path(
        "bdese/<str:siren>/<int:annee>/actualiser-desactualiser",
        views.bdese.toggle_bdese_completion,
        name="toggle_bdese_completion",
    ),
    path("csrd", views.csrd.csrd, name="csrd"),
]
