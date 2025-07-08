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
            statut = IndexEgaproReglementation().calculate_status(caracteristiques)
            if statut.status == ReglementationStatus.STATUS_A_ACTUALISER:
                for utilisateur in entreprise.users.all():
                    print(
                        (entreprise.siren, entreprise.denomination, utilisateur.email)
                    )
