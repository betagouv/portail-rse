from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field

from django.conf import settings
from django.urls import reverse_lazy

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import is_user_attached_to_entreprise


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

    @abstractmethod
    def est_soumis(self, caracteristiques: CaracteristiquesAnnuelles) -> bool:
        pass

    @abstractmethod
    def calculate_status(
        self,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if not user.is_authenticated:
            return self.calculate_status_for_anonymous_user(caracteristiques)
        elif not is_user_attached_to_entreprise(user, self.entreprise):
            return self.calculate_status_for_unauthorized_user(caracteristiques)

    def calculate_status_for_anonymous_user(
        self, caracteristiques: CaracteristiquesAnnuelles
    ):
        if self.est_soumis(caracteristiques):
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

    def calculate_status_for_unauthorized_user(
        self, caracteristiques: CaracteristiquesAnnuelles
    ):
        if self.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_SOUMIS
            status_detail = "L'entreprise est soumise à cette réglementation."
        else:
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "L'entreprise n'est pas soumise à cette réglementation."
        return ReglementationStatus(status, status_detail)
