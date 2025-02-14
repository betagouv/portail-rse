from reglementations.models.csrd import Enjeu
from reglementations.models.csrd import RapportCSRD


def analyse_rapports_csrd():
    print("Nombre rapports créés : ", RapportCSRD.objects.count())
    print(
        "Nombre rapports au moins une étape marquée comme validée : ",
        RapportCSRD.objects.exclude(etape_validee=None).count(),
    )
    print(
        "Nombre rapports étape introduction validée : ",
        RapportCSRD.objects.filter(etape_validee="introduction").count(),
    )
    print(
        "Nombre rapports étape selection-enjeux validée : ",
        RapportCSRD.objects.filter(etape_validee="selection-enjeux").count(),
    )
    print(
        "Nombre rapports étape analyse-materialite validée : ",
        RapportCSRD.objects.filter(etape_validee="analyse-materialite").count(),
    )
    print(
        "Nombre rapports étape collection-donnees-entreprise validée : ",
        RapportCSRD.objects.filter(
            etape_validee="collection-donnees-entreprise"
        ).count(),
    )
    print(
        "Nombre rapports étape redaction-rapport-durabilite validée : ",
        RapportCSRD.objects.filter(
            etape_validee="redaction-rapport-durabilite"
        ).count(),
    )
    print("Nombre rapports publiés : ", RapportCSRD.objects.publies().count())
    enjeux_selectionnes = Enjeu.objects.selectionnes().distinct("rapport_csrd")
    print(
        "Nombre rapports avec au moins un enjeu sélectionné : ",
        enjeux_selectionnes.count(),
    )
    enjeux_analyses = Enjeu.objects.analyses().distinct("rapport_csrd")
    print(
        "Nombre rapports avec au moins un enjeu analysé (matérialité connue) : ",
        enjeux_analyses.count(),
    )
    print("---")
    print("Rapports publiés")
    for rapport in RapportCSRD.objects.publies().all():
        print(rapport)
    print("---")
    print(
        "Rapports avec un enjeu analysé (nombre enjeux sélectionnés, nombre enjeux analysés, nombre enjeux matériels)"
    )
    for enjeu in enjeux_analyses.all():
        rapport = enjeu.rapport_csrd
        print(
            rapport,
            rapport.nombre_enjeux_selectionnes(),
            rapport.enjeux.filter(materiel__isnull=False).count(),
            rapport.enjeux.filter(materiel=True).count(),
        )
    # print("---")
    # print("Rapports avec un enjeu sélectionné")
    # for enjeu in enjeux_selectionnes.all():
    #     rapport = enjeu.rapport_csrd
    #     print(rapport, rapport.nombre_enjeux_selectionnes(), rapport.enjeux.filter(materiel__isnull=False).count())
