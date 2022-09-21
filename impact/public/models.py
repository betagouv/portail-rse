from django.db import models


class BDESE(models.Model):
    # Décret no 2022-678 du 26 avril 202
    annee = models.IntegerField()
    # 1° Investissements
    # 1° A - Investissement social
    # 1° A - a) Evolution des effectifs par type de contrat, par âge, par ancienneté
    # 1° A - a) i - Effectif
    effectif_total = models.IntegerField(
        help_text="Tout salarié inscrit à l’effectif au 31/12 quelle que soit la nature de son contrat de travail",
    )
    effectif_permanent = models.IntegerField(
        help_text="Les salariés à temps plein, inscrits à l’effectif pendant toute l’année considérée et titulaires d’un contrat de travail à durée indéterminée."
    )
    effectif_cdd = models.IntegerField(
        "Effectif CDD",
        help_text="Nombre de salariés titulaires d’un contrat de travail à durée déterminée au 31/12",
    )
    effectif_mensuel_moyen = models.IntegerField(
        help_text="Somme des effectifs totaux mensuels divisée par 12 (on entend par effectif total tout salarié inscrit à l’effectif au dernier jour du mois considéré)"
    )
    effectif_sexe_homme = models.IntegerField()
    effectif_sexe_femme = models.IntegerField()
    effectif_sexe_autre = models.IntegerField()
    effectif_moins_25_ans = models.IntegerField()
    effectif_25_35_ans = models.IntegerField()
    effectif_35_45_ans = models.IntegerField()
    effectif_45_55_ans = models.IntegerField()
    effectif_plus_55_ans = models.IntegerField()
    effectif_anciennete_faible = models.IntegerField()
    effectif_anciennete_moyenne = models.IntegerField()
    effectif_anciennete_forte = models.IntegerField()
    effectif_nationalite_francaise = models.IntegerField()
    effectif_nationalite_etrangere = models.IntegerField()
    effectif_cadres = models.IntegerField()
    effectif_techniciens = models.IntegerField()
    effectif_agents_de_maitrise = models.IntegerField()
    effectif_employes_qualifies = models.IntegerField()
    effectif_employes_non_qualifies = models.IntegerField()
    effectif_ouvriers_qualifies = models.IntegerField()
    effectif_ouvriers_non_qualifies = models.IntegerField()
    # 1° A - a) ii - Travailleurs extérieurs
    nombre_travailleurs_exterieurs = models.IntegerField(
        help_text="Nombre de salariés appartenant à une entreprise extérieure (prestataire de services) dont l’entreprise connaît le nombre, soit parce qu’il figure dans le contrat signé avec l’entreprise extérieure, soit parce que ces travailleurs sont inscrits aux effectifs."
    )
    nombre_stagiaires = models.IntegerField(
        help_text="Stages supérieurs à une semaine."
    )
    nombre_moyen_mensuel_salaries_temporaires = models.IntegerField(
        help_text="Est considérée comme salarié temporaire toute personne mise à la disposition de l’entreprise, par une entreprise de travail temporaire."
    )
    duree_moyenne_contrat_de_travail_temporaire = models.IntegerField()
    nombre_salaries_de_l_entreprise_detaches = models.IntegerField()
    nombre_salaries_detaches_accueillis = models.IntegerField()
    # 1° A - b) Evolution des emplois, notamment, par catégorie professionnelle
    # 1° A - b) i - Embauches
    nombre_embauches_cdi = models.IntegerField()
    nombre_embauches_cdd = models.IntegerField()
    nombre_embauches_saisonniers = models.IntegerField()
    nombre_embauches_jeunes = models.IntegerField(
        help_text="Salariés de moins de 25 ans."
    )
    # 1° A - b) ii - Départs
    total_departs = models.IntegerField()
    nombre_demissions = models.IntegerField()
    nombre_licenciements_economiques = models.IntegerField(
        help_text="Nombre de licenciements pour motif économique, dont départs en retraite et préretraite "
    )
    nombre_licenciements_autres = models.IntegerField(
        help_text="Nombre de licenciements pour d’autres causes"
    )
    nombre_fin_cdd = models.IntegerField()
    nombre_fin_periode_essai = models.IntegerField(
        help_text="Nombre de départs au cours de la période d’essai, à ne remplir que si ces départs sont comptabilisés dans le total des départs."
    )
    nombre_mutations = models.IntegerField(
        help_text="Nombre de mutations d’un établissement à un autre"
    )
    nombre_departs_volontaires_retraite_preretraite = models.IntegerField(
        help_text="Nombre de départs volontaires en retraite et préretraite. Distinguer les différents systèmes légaux et conventionnels de toute nature."
    )
    nombre_deces = models.IntegerField()
    # 1° A - b) iii - Promotions
    nombre_promotions = models.IntegerField(
        help_text="Nombre de salariés promus dans l’année dans une catégorie supérieure. Utiliser les catégories de la nomenclature détaillée."
    )
    # 1° A - b) iv - Chômage
    nombre_salaries_chomage_partiel = models.IntegerField(
        help_text="Nombre de salariés mis en chômage partiel pendant l’année considérée."
    )
    nombre_heures_chomage_partiel_indemnisees = models.IntegerField(
        help_text="Y compris les heures indemnisées au titre du chômage total en cas d’arrêt de plus de quatre semaines consécutives"
    )
    nombre_heures_chomage_partiel_non_indemnisees = models.IntegerField()
    nombre_salaries_chomage_intemperies = models.IntegerField()
    nombre_heures_chomage_intemperies_indemnisees = models.IntegerField()
    nombre_heures_chomage_intemperies_non_indemnisees = models.IntegerField()
    # 1° A - c) Evolution de l’emploi des personnes handicapées et mesures prises pour le développer
    nombre_travailleurs_handicapés = models.IntegerField(
        help_text="Nombre de travailleurs handicapés employés sur l'année considérée, tel qu’il résulte de la déclaration obligatoire prévue à l’article L. 5212-5."
    )
    nombre_travailleurs_handicapes_accidents_du_travail = models.IntegerField(
        help_text="Nombre de travailleurs handicapés à la suite d'accidents du travail intervenus dans l'entreprise, employés sur l'année considérée"
    )
    # 1° A - d) Evolution du nombre de stagiaires
    # 1° A - e) Formation professionnelle : investissements en formation, publics concernés
    # 1° A - e) i - Formation professionnelle continue
    # Conformément aux données relatives aux contributions de formation professionnelle de la déclaration sociale nominative.
    pourcentage_masse_salariale_formation_continue = models.IntegerField(
        help_text="Pourcentage de la masse salariale afférent à la formation continue"
    )
    montant_formation_interne = models.FloatField(
        help_text="Montant consacré à la formation interne"
    )
    montant_formation_conventions = models.FloatField(
        help_text="Montant consacré à la formation effectuée en application de conventions"
    )
    montant_formation_organismes_recouvrement = models.FloatField(
        help_text="Montant du versement aux organismes de recouvrement "
    )
    montant_formation_organismes_agrees = models.FloatField(
        help_text="Montant du versement auprès d'organismes agréés"
    )
    montant_formation_autres = models.FloatField()
    # Nombre de stagiaires (II)
    # Nombre d'heures de stage (II) rémunérées
    # Nombre d'heures de stage (II) non rémunérées
    # Décomposition par type de stages à titre d'exemple : adaptation, formation professionnelle, entretien ou perfectionnement des connaissances
    # 1° A - e) ii - Congés formation
    nombre_salaries_conge_formation_remunere = models.IntegerField(
        help_text="Nombre de salariés ayant bénéficié d'un congé formation rémunéré"
    )
    nombre_salaries_conge_formation_non_remunere = models.IntegerField(
        help_text="Nombre de salariés ayant bénéficié d'un congé formation non rémunéré"
    )
    nombre_salaries_conge_formation_refuse = models.IntegerField(
        help_text="Nombre de salariés auxquels a été refusé un congé formation"
    )
    # 1° A - e) iii - Apprentissage
    nombre_contrats_apprentissage = models.IntegerField(
        help_text="Nombre de contrats d’apprentissage conclus dans l’année"
    )
    # 1° A - f) Conditions de travail
    # Durée du travail dont travail à temps partiel et aménagement du temps de travail, 
    # les données sur l'exposition aux risques et aux facteurs de pénibilité, 
    # (accidents du travail, maladies professionnelles, absentéisme, dépenses en matière de sécurité)
    # 1° A - f) i - Accidents du travail et de trajet
    # 1° A - f) ii - Répartition des accidents par éléments matériels
    # 1° A - f) iii - Maladies professionnelles
    # 1° A - f) iv - Dépenses en matière de sécurité
    # 1° A - f) v - Durée et aménagement du temps de travail
    # 1° A - f) vi - Absentéisme
    # 1° A - f) vii - Organisation et contenu du travail
    # 1° A - f) viii - Conditions physiques de travail
    # 1° A - f) ix - Transformation de l’organisation du travail
    # 1° A - f) x - Dépenses d’amélioration de conditions de travail
    # 1° A - f) xi - Médecine du travail
    # 1° A - f) xii - Travailleurs inaptes
    # 1° B - Investissement matériel et immatériel
    # 1° B - a) Evolution des actifs nets d’amortissement et de dépréciations éventuelles (immobilisations)
    # 1° B - b) Le cas échéant, dépenses de recherche et développement
    # 1° B - c) L’évolution de la productivité et le taux d’utilisation des capacités de production, lorsque ces éléments sont mesurables dans l’entreprise


   ###########################################################

   # 2° Egalité professionnelle entre les femmes et les hommes au sein de l'entreprise
   # I. Indicateurs sur la situation comparée des femmes et des hommes dans l'entreprise
   # a) Effectifs : Données chiffrées par sexe :
   # Répartition par catégorie professionnelle selon les différents contrats de travail (CDI ou CDD) ;