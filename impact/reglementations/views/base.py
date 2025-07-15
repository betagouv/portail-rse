from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field

from entreprises.models import CaracteristiquesAnnuelles


class InsuffisammentQualifieeError(Exception):
    pass


@dataclass
class ReglementationAction:
    url: str
    title: str
    external: bool = False


@dataclass
class ReglementationStatus:
    STATUS_A_ACTUALISER = 0
    STATUS_EN_COURS = 1
    STATUS_A_JOUR = 2
    STATUS_SOUMIS = 3
    STATUS_NON_SOUMIS = 4
    STATUS_RECOMMANDE = 5
    STATUS_INCALCULABLE = 1000

    status: int
    status_detail: str
    prochaine_echeance: str | None = None
    primary_action: ReglementationAction | None = None
    secondary_actions: list[ReglementationAction] = field(default_factory=list)


class Reglementation(ABC):
    title: str
    more_info_url: str
    summary: str
    tag: str
    zone: str = "france"

    @classmethod
    def info(cls):
        return {
            "title": cls.title,
            "more_info_url": cls.more_info_url,
            "tag": cls.tag,
            "summary": cls.summary,
            "zone": cls.zone,
        }

    @classmethod
    @abstractmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        pass

    @classmethod
    @abstractmethod
    def criteres_remplis(cls, caracteristiques):
        pass

    @classmethod
    @abstractmethod
    def est_soumis(cls, caracteristiques: CaracteristiquesAnnuelles) -> bool:
        if not cls.est_suffisamment_qualifiee(caracteristiques):
            raise InsuffisammentQualifieeError

    @classmethod
    @abstractmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
    ) -> ReglementationStatus:
        if not cls.est_suffisamment_qualifiee(caracteristiques):
            primary_action = ReglementationAction(
                "/qualification", "Qualifier mon entreprise"
            )
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_INCALCULABLE,
                status_detail="Impossible de connaitre l'état de cette réglementation",
                primary_action=primary_action,
            )
