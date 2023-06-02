from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import CSS
from weasyprint import HTML

from api import egapro
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import get_habilitation
from habilitations.models import is_user_attached_to_entreprise
from habilitations.models import is_user_habilited_on_entreprise
from public.forms import EligibiliteForm
from reglementations.forms import bdese_configuration_form_factory
from reglementations.forms import bdese_form_factory
from reglementations.forms import IntroductionDemoForm
from reglementations.models import annees_a_remplir_bdese
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.models import derniere_annee_a_remplir_bdese
from reglementations.models import derniere_annee_a_remplir_index_egapro


@dataclass
class ReglementationAction:
    url: str
    title: str
    external: bool = False


@dataclass
class ReglementationStatus:
    STATUS_NON_SOUMIS = "non soumis"
    STATUS_SOUMIS = "soumis"
    STATUS_A_JOUR = "à jour"
    STATUS_A_ACTUALISER = "à actualiser"
    STATUS_EN_COURS = "en cours"

    status: str
    status_detail: str
    primary_action: ReglementationAction | None = None
    secondary_actions: list[ReglementationAction] = field(default_factory=list)


class Reglementation(ABC):
    title: str
    description: str
    more_info_url: str

    def __init__(self, entreprise) -> None:
        super().__init__()
        self.entreprise = entreprise

    @classmethod
    def info(cls):
        return {
            "title": cls.title,
            "description": cls.description,
            "more_info_url": cls.more_info_url,
        }

    @property
    @abstractmethod
    def is_soumis(self):
        pass

    @abstractmethod
    def calculate_status(
        self,
        annee: int,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if not user.is_authenticated:
            if self.is_soumis:
                status = ReglementationStatus.STATUS_SOUMIS
                login_url = f"{reverse_lazy('users:login')}?next={reverse_lazy('reglementations:reglementations', args=[self.entreprise.siren])}"
                status_detail = f'<a href="{login_url}">Vous êtes soumis à cette réglementation. Connectez-vous pour en savoir plus.</a>'
                primary_action = ReglementationAction(login_url, f"Se connecter")
            else:
                status = ReglementationStatus.STATUS_NON_SOUMIS
                status_detail = "Vous n'êtes pas soumis à cette réglementation."
                primary_action = None
            return ReglementationStatus(
                status, status_detail, primary_action=primary_action
            )
        elif not is_user_attached_to_entreprise(user, self.entreprise):
            if self.is_soumis:
                status = ReglementationStatus.STATUS_SOUMIS
                status_detail = "L'entreprise est soumise à cette réglementation."
            else:
                status = ReglementationStatus.STATUS_NON_SOUMIS
                status_detail = "L'entreprise n'est pas soumise à cette réglementation."
            return ReglementationStatus(status, status_detail)


class BDESEReglementation(Reglementation):
    TYPE_AVEC_ACCORD = 1
    TYPE_INFERIEUR_300 = 2
    TYPE_INFERIEUR_500 = 3
    TYPE_SUPERIEUR_500 = 4

    title = "Base de données économiques, sociales et environnementales (BDESE)"
    description = """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        En l'absence d'accord d'entreprise spécifique, elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    more_info_url = "https://entreprendre.service-public.fr/vosdroits/F32193"

    def bdese_type(self) -> int:
        effectif = self.entreprise.effectif
        if self.entreprise.bdese_accord:
            return self.TYPE_AVEC_ACCORD
        elif effectif == Entreprise.EFFECTIF_ENTRE_50_ET_299:
            return self.TYPE_INFERIEUR_300
        elif effectif == Entreprise.EFFECTIF_ENTRE_300_ET_499:
            return self.TYPE_INFERIEUR_500
        elif effectif == Entreprise.EFFECTIF_500_ET_PLUS:
            return self.TYPE_SUPERIEUR_500

    @property
    def is_soumis(self):
        return self.entreprise.effectif != Entreprise.EFFECTIF_MOINS_DE_50

    def calculate_status(
        self, annee: int, user: settings.AUTH_USER_MODEL
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(annee, user):
            return reglementation_status

        for match in [
            self._match_non_soumis,
            self._match_avec_accord,
            self._match_bdese_existante,
            self._match_sans_bdese,
        ]:
            if reglementation_status := match(annee, user):
                return reglementation_status

    def _match_non_soumis(self, annee, user):
        if not self.is_soumis:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            return ReglementationStatus(status, status_detail)

    def _match_avec_accord(self, annee, user):
        if self.bdese_type() == self.TYPE_AVEC_ACCORD:
            bdese = self._select_bdese(BDESEAvecAccord, annee, user)
            if bdese and bdese.is_complete:
                status = ReglementationStatus.STATUS_A_JOUR
                primary_action_title = f"Marquer ma BDESE {annee} comme non actualisée"
            else:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                primary_action_title = f"Marquer ma BDESE {annee} comme actualisée"

            status_detail = "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:toggle_bdese_completion",
                    args=[self.entreprise.siren, annee],
                ),
                primary_action_title,
            )
            return ReglementationStatus(
                status,
                status_detail,
                primary_action=primary_action,
            )

    def _match_bdese_existante(self, annee, user):
        if self.bdese_type() == self.TYPE_INFERIEUR_300:
            bdese_class = BDESE_50_300
        else:
            bdese_class = BDESE_300

        bdese = self._select_bdese(bdese_class, annee, user)
        if not bdese:
            return

        if bdese.is_complete:
            status = ReglementationStatus.STATUS_A_JOUR
            status_detail = f"Vous êtes soumis à cette réglementation. Vous avez actualisé votre BDESE {annee} sur la plateforme."
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:bdese_pdf", args=[self.entreprise.siren, annee]
                ),
                f"Télécharger le pdf {annee}",
                external=True,
            )
            secondary_actions = [
                ReglementationAction(
                    reverse_lazy(
                        "reglementations:bdese", args=[self.entreprise.siren, annee, 1]
                    ),
                    "Modifier ma BDESE",
                )
            ]
        else:
            status = ReglementationStatus.STATUS_EN_COURS
            status_detail = f"Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE {annee} sur la plateforme."
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:bdese", args=[self.entreprise.siren, annee, 1]
                ),
                "Reprendre l'actualisation de ma BDESE",
            )
            secondary_actions = [
                ReglementationAction(
                    reverse_lazy(
                        "reglementations:bdese_pdf", args=[self.entreprise.siren, annee]
                    ),
                    f"Télécharger le pdf {annee} (brouillon)",
                    external=True,
                ),
            ]

        return ReglementationStatus(
            status,
            status_detail,
            primary_action=primary_action,
            secondary_actions=secondary_actions,
        )

    def _match_sans_bdese(self, annee, user):
        status = ReglementationStatus.STATUS_A_ACTUALISER
        status_detail = "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
        primary_action = ReglementationAction(
            reverse_lazy(
                "reglementations:bdese", args=[self.entreprise.siren, annee, 0]
            ),
            "Actualiser ma BDESE",
        )
        secondary_actions = []
        return ReglementationStatus(
            status,
            status_detail,
            primary_action=primary_action,
            secondary_actions=secondary_actions,
        )

    def _select_bdese(self, bdese_class, annee, user):
        if (
            user
            and is_user_attached_to_entreprise(user, self.entreprise)
            and not is_user_habilited_on_entreprise(user, self.entreprise)
        ):
            bdese = bdese_class.personals.filter(
                entreprise=self.entreprise, annee=annee, user=user
            )
        else:
            bdese = bdese_class.officials.filter(
                entreprise=self.entreprise, annee=annee
            )

        return bdese[0] if bdese else None


class IndexEgaproReglementation(Reglementation):
    title = "Index de l’égalité professionnelle"
    description = "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    more_info_url = "https://www.economie.gouv.fr/entreprises/index-egalite-professionnelle-obligatoire"

    @property
    def is_soumis(self):
        return self.entreprise.effectif != Entreprise.EFFECTIF_MOINS_DE_50

    def calculate_status(
        self, annee: int, user: settings.AUTH_USER_MODEL
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(annee, user):
            return reglementation_status

        PRIMARY_ACTION = ReglementationAction(
            "https://egapro.travail.gouv.fr/",
            "Calculer et déclarer mon index sur Egapro",
            external=True,
        )
        if self.entreprise.effectif == Entreprise.EFFECTIF_MOINS_DE_50:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
        elif is_index_egapro_updated(self.entreprise):
            status = ReglementationStatus.STATUS_A_JOUR
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
        else:
            status = ReglementationStatus.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
        return ReglementationStatus(
            status, status_detail, primary_action=PRIMARY_ACTION
        )


def is_index_egapro_updated(entreprise: Entreprise) -> bool:
    year = derniere_annee_a_remplir_index_egapro()
    return egapro.is_index_egapro_updated(entreprise.siren, year)


def reglementations(request):
    entreprise = None

    if request.GET:
        form = EligibiliteForm(request.GET)
        if "siren" in form.data:
            if entreprises := Entreprise.objects.filter(siren=form.data["siren"]):
                entreprise = entreprises[0]
                form = EligibiliteForm(request.GET, instance=entreprise)
                commit = (
                    request.user.is_authenticated
                    and request.user in entreprise.users.all()
                )
            else:
                commit = True

            if form.is_valid():
                request.session["siren"] = form.cleaned_data["siren"]
                entreprise = form.save(commit=commit)

    elif entreprise := get_current_entreprise(request):
        return redirect("reglementations:reglementations", siren=entreprise.siren)

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(entreprise, request.user),
    )


@login_required
def reglementations_for_entreprise(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    request.session["entreprise"] = entreprise.siren

    if not entreprise.is_qualified:
        messages.warning(
            request,
            "Veuillez renseigner les informations suivantes pour connaître les réglementations auxquelles est soumise cette entreprise",
        )
        return redirect("entreprises:qualification", siren=entreprise.siren)

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(entreprise, request.user),
    )


def _reglementations_context(entreprise, user):
    reglementations = [
        {
            "info": BDESEReglementation.info(),
            "status": BDESEReglementation(entreprise).calculate_status(
                derniere_annee_a_remplir_bdese(), user
            )
            if entreprise
            else None,
        },
        {
            "info": IndexEgaproReglementation.info(),
            "status": IndexEgaproReglementation(entreprise).calculate_status(
                derniere_annee_a_remplir_index_egapro(), user
            )
            if entreprise
            else None,
        },
    ]
    return {
        "entreprise": entreprise,
        "reglementations": reglementations,
    }


@login_required
def bdese_pdf(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied
    bdese = _get_or_create_bdese(entreprise, annee, request.user)
    pdf_html = render_bdese_pdf_html(bdese)
    html = HTML(string=pdf_html)
    css = CSS(
        string="""
        @font-face {
            font-family: 'Marianne';
            src: url('../../static/fonts/Marianne/fontes desktop/Marianne-Regular.otf');
        }
        @page {
            font-family: 'Marianne';
        }
        body {
            font-family: 'Marianne';
        }
    """
    )
    pdf_file = html.write_pdf(stylesheets=[css])

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'filename="bdese.pdf"'
    return response


def render_bdese_pdf_html(bdese):
    context = {"bdese": bdese}
    template_path = _pdf_template_path_from_bdese(bdese)
    pdf_html = render_to_string(template_path, context)
    return pdf_html


def _pdf_template_path_from_bdese(bdese):
    if bdese.is_bdese_300:
        return "reglementations/bdese_300_pdf.html"
    else:
        return "reglementations/bdese_50_300_pdf.html"


def get_bdese_data_from_egapro(entreprise: Entreprise, year: int) -> dict:
    return egapro.indicateurs(entreprise.siren, year)


@login_required
def bdese(request, siren, annee, step):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    bdese = _get_or_create_bdese(entreprise, annee, request.user)

    if not bdese.is_configured and step != 0:
        messages.warning(request, f"Commencez par configurer votre BDESE {annee}")
        return redirect("reglementations:bdese", siren=siren, annee=annee, step=0)

    if request.method == "POST":
        if "mark_incomplete" in request.POST:
            bdese.mark_step_as_incomplete(step)
            bdese.save()
            return redirect(
                "reglementations:bdese", siren=siren, annee=annee, step=step
            )
        else:
            if step == 0:
                form = bdese_configuration_form_factory(bdese, data=request.POST)
            else:
                form = bdese_form_factory(
                    bdese,
                    step,
                    data=request.POST,
                )
            if form.is_valid():
                bdese = form.save()
                messages.success(request, "Étape enregistrée")
                if "save_complete" in request.POST:
                    bdese.mark_step_as_complete(step)
                    bdese.save()
                    if step < len(bdese.STEPS) - 1:
                        step += 1
                return redirect(
                    "reglementations:bdese", siren=siren, annee=annee, step=step
                )
            else:
                messages.error(
                    request,
                    "L'étape n'a pas été enregistrée car le formulaire contient des erreurs",
                )

    else:
        if step == 0:
            initial = None
            if not bdese.is_configured:
                initial = initialize_bdese_configuration(bdese)
            form = bdese_configuration_form_factory(
                bdese,
                initial=initial,
            )
        else:
            fetched_data = get_bdese_data_from_egapro(entreprise, annee)
            form = bdese_form_factory(
                bdese,
                step,
                fetched_data=fetched_data,
            )

    if (
        not is_user_habilited_on_entreprise(request.user, entreprise)
        and entreprise.users.count() >= 2
    ):
        messages.info(
            request,
            "Plusieurs utilisateurs sont liés à cette entreprise. Les informations que vous remplissez ne sont pas partagées avec les autres utilisateurs tant que vous n'êtes pas habilités.",
        )

    return render(
        request,
        _bdese_step_template_path(bdese, step),
        _bdese_step_context(form, siren, annee, bdese, step),
    )


def _bdese_step_template_path(bdese: BDESE_300 | BDESE_50_300, step: int) -> str:
    if step == 0:
        directory = ""
        template_file = "0_categories_professionnelles.html"
    else:
        if bdese.is_bdese_300:
            directory = "bdese_300/"
        else:
            directory = "bdese_50_300/"
        templates = {
            1: "1_investissement_social.html",
            2: "2_investissement_matériel_et_immatériel.html",
            3: "3_egalite_professionnelle.html",
            4: "4_fonds_propres_endettement_impots.html",
            5: "5_remuneration.html",
            6: "6_representation_du_personnel_et_activites_sociales_et_culturelles.html",
            7: "7_remuneration_des_financeurs.html",
            8: "8_flux_financiers.html",
            9: "9_partenariats.html",
            10: "10_transferts_commerciaux_et_financiers.html",
            11: "11_environnement.html",
        }
        template_file = templates[step]
    return f"reglementations/{directory}{template_file}"


def _bdese_step_context(form, siren, annee, bdese, step):
    steps = {
        step: {
            "name": bdese.STEPS[step],
            "is_complete": bdese.step_is_complete(step),
        }
        for step in bdese.STEPS
    }
    step_is_complete = steps[step]["is_complete"]
    bdese_is_complete = bdese.is_complete
    context = {
        "form": form,
        "siren": siren,
        "annee": annee,
        "step_is_complete": step_is_complete,
        "steps": steps,
        "bdese_is_complete": bdese_is_complete,
        "annees": annees_a_remplir_bdese(),
    }
    if step == 0:
        context["demo_form"] = IntroductionDemoForm()
    return context


def _get_or_create_bdese(
    entreprise: Entreprise,
    annee: int,
    user: settings.AUTH_USER_MODEL,
) -> BDESE_300 | BDESE_50_300 | BDESEAvecAccord:
    bdese_type = BDESEReglementation(entreprise).bdese_type()
    habilitation = get_habilitation(user, entreprise)
    if bdese_type == BDESEReglementation.TYPE_AVEC_ACCORD:
        bdese_class = BDESEAvecAccord
    elif bdese_type in (
        BDESEReglementation.TYPE_INFERIEUR_500,
        BDESEReglementation.TYPE_SUPERIEUR_500,
    ):
        bdese_class = BDESE_300
    else:
        bdese_class = BDESE_50_300

    if habilitation.is_confirmed:
        bdese, _ = bdese_class.officials.get_or_create(
            entreprise=entreprise, annee=annee
        )
    else:
        bdese, _ = bdese_class.personals.get_or_create(
            entreprise=entreprise, annee=annee, user=user
        )

    return bdese


def initialize_bdese_configuration(bdese: BDESE_300 | BDESE_50_300) -> dict:
    bdeses = bdese.__class__.objects.filter(
        entreprise=bdese.entreprise, user=bdese.user
    ).order_by("-annee")
    for _bdese in bdeses:
        if _bdese.categories_professionnelles:
            initial = {
                "categories_professionnelles": _bdese.categories_professionnelles
            }
            if _bdese.is_bdese_300:
                initial[
                    "categories_professionnelles_detaillees"
                ] = _bdese.categories_professionnelles_detaillees
                initial["niveaux_hierarchiques"] = _bdese.niveaux_hierarchiques
            return initial


def toggle_bdese_completion(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    bdese = _get_or_create_bdese(entreprise, annee, request.user)

    if bdese.is_bdese_avec_accord:
        bdese.toggle_completion()
        bdese.save()
        if bdese.is_complete:
            success_message = "La BDESE a été marquée comme actualisée"
        else:
            success_message = "La BDESE a été marquée comme non actualisée"
        messages.success(request, success_message)
    return redirect("reglementations:reglementations", siren=bdese.entreprise.siren)
