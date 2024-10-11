import datetime


def derniere_annee_a_publier_index_egapro():
    annee = datetime.date.today().year
    return annee - 1


def prochaine_echeance_index_egapro(derniere_annee_est_publiee: bool) -> datetime.date:
    aujourdhui = datetime.date.today()
    annee = aujourdhui.year
    if derniere_annee_est_publiee:
        return datetime.date(annee + 1, 3, 1)
    else:
        return datetime.date(annee, 3, 1)
