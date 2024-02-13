from entreprises.models import Entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.index_egapro import IndexEgaproReglementation


def entreprises_avec_index_egapro_en_retard():
    for entreprise in Entreprise.objects.all():
        caracteristiques = (
            entreprise.dernieres_caracteristiques_qualifiantes
            or entreprise.dernieres_caracteristiques
        )
        if (
            entreprise.users.all()
            and caracteristiques
            and IndexEgaproReglementation().est_suffisamment_qualifiee(caracteristiques)
        ):
            for utilisateur in entreprise.users.all():
                statut = IndexEgaproReglementation().calculate_status(
                    caracteristiques, utilisateur
                )
                if statut.status == ReglementationStatus.STATUS_A_ACTUALISER:
                    print(
                        (entreprise.siren, entreprise.denomination, utilisateur.email)
                    )
