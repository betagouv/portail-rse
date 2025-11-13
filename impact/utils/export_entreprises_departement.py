"""fonction d'export des entreprises inscrites actives (ayant commencé un rapport VSME) d'un département

affiche les résultats dans le terminal pour faciliter son usage avec scalingo :
scalingo --region REGION --app APP run python3 impact/manage.py shell
"""

import time

from django.db.models import Count

from entreprises.models import Entreprise
from utils.origine_departement import extrait_departement
from utils.origine_departement import recup_donnees


def entreprises_du_departement(numero_departement):
    print("siren,code postal,coordonnees,nb indicateurs dernier rapport vsme,email")
    compteur = 0
    for entreprise in Entreprise.objects.filter(
        users__isnull=False, rapports_vsme__isnull=False
    ).distinct():
        # On ne récupère que les entreprises inscrites qui ont commencé un rapport VSME
        succes, donnees = recup_donnees(entreprise.siren)
        if succes:
            code_postal = donnees["code_postal"]
            if extrait_departement(code_postal) == str(numero_departement):
                dernier_rapport = (
                    entreprise.rapports_vsme.annotate(
                        nb_indicateurs=Count("indicateurs"),
                    )
                    .order_by("-annee")
                    .first()
                )
                for utilisateur in entreprise.users.all():
                    print(
                        f"{entreprise.siren},{code_postal},{donnees["coordonnees"]},{dernier_rapport.nb_indicateurs},{utilisateur.email}"
                    )
        else:
            print(donnees)
        compteur += 1
        if compteur % 100 == 0:
            print(f"{compteur} ENTREPRISES RECHERCHEES")
        time.sleep(
            0.15
        )  # Limite de 7 appels/seconde à l'API Recherche d'Entreprises utilisée par recup_donnees
