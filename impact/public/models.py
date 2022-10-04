from django import forms
from django.db import models


class Entreprise(models.Model):
    siren = models.CharField(max_length=9)

    def __str__(self):
        return self.siren


class CategoryField(models.JSONField):
    def __init__(self, base_field=forms.IntegerField, categories=None, *args, **kwargs):
        self.base_field = base_field
        self.categories = categories
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["base_field"] = self.base_field
        if self.categories:
            kwargs["categories"] = self.categories
        return name, path, args, kwargs

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + ("base_field", "categories",)

    def formfield(self, **kwargs):
        defaults = {
            "base_field": self.base_field,
        }
        if self.categories:
            defaults["categories"] = self.categories
        defaults.update(kwargs)
        return super().formfield(**defaults)


def categories_default():
    return ["ouvrier", "employé", "technicien", "agent de maitrise", "cadre"]


class BDESE(models.Model):
    annee = models.IntegerField(default=2022)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)

    def __str__(self):
        return self.entreprise.siren

    @classmethod
    def category_fields(cls):
        return [
            attribute_name
            for attribute_name
            in cls.__dict__.keys()
            if hasattr(getattr(BDESE, attribute_name), "field") and type(getattr(BDESE, attribute_name).field) == CategoryField
        ]

    # Décret no 2022-678 du 26 avril 2022
    # 1° Investissements
    # 1° A - Investissement social
    # 1° A - a) Evolution des effectifs par type de contrat, par âge, par ancienneté
    # 1° A - a) i - Effectif
    effectif_total = CategoryField(
        help_text="Tout salarié inscrit à l’effectif au 31/12 quelle que soit la nature de son contrat de travail",
        null=True,
        blank=True,
    )
    effectif_permanent = CategoryField(
        help_text="Les salariés à temps plein, inscrits à l’effectif pendant toute l’année considérée et titulaires d’un contrat de travail à durée indéterminée.",
        null=True,
        blank=True,
    )
    effectif_cdd = CategoryField(
        verbose_name="Effectif CDD",
        help_text="Nombre de salariés titulaires d’un contrat de travail à durée déterminée au 31/12",
        blank=True,
        null=True,
    )
    effectif_mensuel_moyen = CategoryField(
        help_text="Somme des effectifs totaux mensuels divisée par 12 (on entend par effectif total tout salarié inscrit à l’effectif au dernier jour du mois considéré)",
        null=True,
        blank=True,
    )
    effectif_homme = CategoryField(
        null=True,
        blank=True,
    )
    effectif_femme = CategoryField(
        null=True,
        blank=True,
    )
    effectif_age = CategoryField(
        categories=["moins de 25 ans", "entre 25 et 35 ans", "entre 35 et 45 ans", "entre 45 et 55 ans", "plus de 55 ans"],
        verbose_name="Effectif par âge",
        null=True,
        blank=True,
    )
    effectif_anciennete = CategoryField(
        categories=["moins de 10 ans", "entre 10 et 20 ans", "plus de 30 ans"],
        verbose_name="Effectif par ancienneté",
        null=True,
        blank=True,
    )
    effectif_nationalite_francaise = CategoryField(
        verbose_name="Effectif de nationalité française",
        null=True,
        blank=True,
    )
    effectif_nationalite_etrangere = CategoryField(
        verbose_name="Effectif de nationalité étrangère",
        null=True,
        blank=True,
    )
    # effectif_cadres = models.IntegerField()
    # effectif_techniciens = models.IntegerField()
    # effectif_agents_de_maitrise = models.IntegerField()
    # effectif_employes_qualifies = models.IntegerField()
    # effectif_employes_non_qualifies = models.IntegerField()
    # effectif_ouvriers_qualifies = models.IntegerField()
    # effectif_ouvriers_non_qualifies = models.IntegerField()
    # 1° A - a) ii - Travailleurs extérieurs
    nombre_travailleurs_exterieurs = models.IntegerField(
        verbose_name="Nombre de travailleurs extérieurs",
        help_text="Nombre de salariés appartenant à une entreprise extérieure (prestataire de services) dont l’entreprise connaît le nombre, soit parce qu’il figure dans le contrat signé avec l’entreprise extérieure, soit parce que ces travailleurs sont inscrits aux effectifs.",
        null=True,
        blank=True,
    )
    nombre_stagiaires = models.IntegerField(
        verbose_name="Nombre de stagiaires",
        help_text="Stages supérieurs à une semaine.",
        null=True,
        blank=True,
    )
    nombre_moyen_mensuel_salaries_temporaires = models.IntegerField(
        verbose_name="Nombre moyen mensuel de salariés temporaires",
        help_text="Est considérée comme salarié temporaire toute personne mise à la disposition de l’entreprise, par une entreprise de travail temporaire.",
        null=True,
        blank=True,
    )
    duree_moyenne_contrat_de_travail_temporaire = models.IntegerField(
        verbose_name="Durée moyenne des contrats de travail temporaire",
        help_text="En jours",
        null=True,
        blank=True,
    )
    nombre_salaries_de_l_entreprise_detaches = models.IntegerField(
        verbose_name="Nombre de salariés de l'entreprise détachés",
        null=True,
        blank=True,
    )
    nombre_salaries_detaches_accueillis = models.IntegerField(
        verbose_name="Nombre de salariés détachés accueillis",
        null=True,
        blank=True,
    )
    # 1° A - b) Evolution des emplois, notamment, par catégorie professionnelle
    # 1° A - b) i - Embauches
    nombre_embauches_cdi = models.IntegerField(
        verbose_name="Nombre d'embauches par contrats de travail à durée indéterminée",
        null=True,
        blank=True,
    )
    nombre_embauches_cdd = CategoryField(
        verbose_name="Nombre d'embauches par contrats de travail à durée déterminée",
        help_text="dont nombre de contrats de travailleurs saisonniers",
        null=True,
        blank=True,
    )
    nombre_embauches_jeunes = models.IntegerField(
        verbose_name="Nombre d'embauches de salariés de moins de vingt-cinq ans",
        null=True,
        blank=True,
    )
    # 1° A - b) ii - Départs
    total_departs = CategoryField(
        verbose_name="Total des départs",
        null=True,
        blank=True,
    )
    nombre_demissions = CategoryField(
        verbose_name="Nombre de démissions",
        null=True,
        blank=True,
    )
    nombre_licenciements_economiques = CategoryField(
        verbose_name="Nombre de licenciements pour motif économique",
        help_text="dont départs en retraite et préretraite",
        null=True,
        blank=True,
    )
    nombre_licenciements_autres = CategoryField(
        verbose_name="Nombre de licenciements pour d’autres causes",
        null=True,
        blank=True,
    )
    nombre_fin_cdd = CategoryField(
        verbose_name="Nombre de fins de contrats de travail à durée déterminée",
        null=True,
        blank=True,
    )
    nombre_fin_periode_essai = CategoryField(
        verbose_name="Nombre de départs au cours de la période d’essai",
        help_text="à ne remplir que si ces départs sont comptabilisés dans le total des départs",
        null=True,
        blank=True,
    )
    nombre_mutations = CategoryField(
        verbose_name="Nombre de mutations d’un établissement à un autre",
        null=True,
        blank=True,
    )
    nombre_departs_volontaires_retraite_preretraite = models.TextField(
        verbose_name="Nombre de départs volontaires en retraite et préretraite",
        help_text="Distinguer les différents systèmes légaux et conventionnels de toute nature",
        null=True,
        blank=True,
    )
    nombre_deces = CategoryField(
        verbose_name="Nombre de décès",
        null=True,
        blank=True,
    )
    # 1° A - b) iii - Promotions
    nombre_promotions = models.IntegerField(
        verbose_name="Nombre de salariés promus dans l’année dans une catégorie supérieure",
        help_text="Utiliser les catégories de la nomenclature détaillée",
        null=True,
        blank=True,
    )
    # 1° A - b) iv - Chômage
    nombre_salaries_chomage_partiel = CategoryField(
        verbose_name="Nombre de salariés mis en chômage partiel pendant l’année considérée",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_partiel_indemnisees = CategoryField(
        verbose_name="Nombre total d'heures de chômage partiel indemnisées",
        help_text="Y compris les heures indemnisées au titre du chômage total en cas d’arrêt de plus de quatre semaines consécutives",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_partiel_non_indemnisees = CategoryField(
        verbose_name="Nombre total d'heures de chômage partiel non indemnisées",
        null=True,
        blank=True,
    )
    nombre_salaries_chomage_intemperies = CategoryField(
        verbose_name="Nombre de salariés mis en chômage intempéries",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_intemperies_indemnisees = CategoryField(
        verbose_name="Nombre total d'heures de chômage intempéries indemnisées",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_intemperies_non_indemnisees = CategoryField(
        verbose_name="Nombre total d'heures de chômage intempéries non indemnisées",
        null=True,
        blank=True,
    )
    # 1° A - c) Evolution de l’emploi des personnes handicapées et mesures prises pour le développer
    nombre_travailleurs_handicapés = models.IntegerField(
        verbose_name="Nombre de travailleurs handicapés employés sur l'année considérée",
        help_text="tel qu’il résulte de la déclaration obligatoire prévue à l’article L. 5212-5.",
        null=True,
        blank=True,
    )
    nombre_travailleurs_handicapes_accidents_du_travail = models.IntegerField(
        verbose_name="Nombre de travailleurs handicapés à la suite d'accidents du travail intervenus dans l'entreprise",
        help_text="employés sur l'année considérée",
        null=True,
        blank=True,
    )
    # 1° A - d) Evolution du nombre de stagiaires
    # 1° A - e) Formation professionnelle : investissements en formation, publics concernés
    # 1° A - e) i - Formation professionnelle continue
    # Conformément aux données relatives aux contributions de formation professionnelle de la déclaration sociale nominative.
    pourcentage_masse_salariale_formation_continue = models.FloatField(
        verbose_name="Pourcentage de la masse salariale afférent à la formation continue",
        null=True,
        blank=True,
    )
    montant_formation_continue = CategoryField(
        categories=["formation interne", "formation effectuée en application de conventions", "versement aux organismes de recouvrement", "versement auprès d'organismes agréés", "autres"],
        verbose_name="Montant consacré à la formation continue",
        null=True,
        blank=True,
    )
    # Nombre de stagiaires (II)
    nombre_heures_stage_remunerees = models.IntegerField(
        verbose_name="Nombre d'heures de stage rémunérées",
        null=True,
        blank=True,
    )
    nombre_heures_stage_non_remunerees = models.IntegerField(
        verbose_name="Nombre d'heures de stage non rémunérées",
        null=True,
        blank=True,
    )
    type_stages = models.TextField(
        verbose_name="Décomposition par type de stages",
        help_text="à titre d'exemple : adaptation, formation professionnelle, entretien ou perfectionnement des connaissances",
        null=True,
        blank=True,
    )
    # 1° A - e) ii - Congés formation
    nombre_salaries_conge_formation_remunere = models.IntegerField(
        verbose_name="Nombre de salariés ayant bénéficié d'un congé formation rémunéré",
        null=True,
        blank=True,
    )
    nombre_salaries_conge_formation_non_remunere = models.IntegerField(
        verbose_name="Nombre de salariés ayant bénéficié d'un congé formation non rémunéré",
        null=True,
        blank=True,
    )
    nombre_salaries_conge_formation_refuse = models.IntegerField(
        verbose_name="Nombre de salariés auxquels a été refusé un congé formation",
        null=True,
        blank=True,
    )
    # 1° A - e) iii - Apprentissage
    nombre_contrats_apprentissage = models.IntegerField(
        verbose_name="Nombre de contrats d’apprentissage conclus dans l’année",
        null=True,
        blank=True,
    )
class Vide:
    # 1° A - f) Conditions de travail
    # Durée du travail dont travail à temps partiel et aménagement du temps de travail,
    # les données sur l'exposition aux risques et aux facteurs de pénibilité,
    # (accidents du travail, maladies professionnelles, absentéisme, dépenses en matière de sécurité)
    # 1° A - f) i - Accidents du travail et de trajet
    taux_frequence_accidents_travail = models.IntegerField(
        verbose_name="Taux de fréquence des accidents du travail"
    )
    nombre_accidents_travail_par_heure_travaillee = models.IntegerField(
        verbose_name="Nombre d'accidents avec arrêts de travail divisé par nombre d'heures travaillées"
    )
    taux_gravite_accidents_travail = models.IntegerField(
        verbose_name="Taux de gravité des accidents du travail"
    )
    nombre_journees_perdues_par_heure_travaillee = models.IntegerField(
        verbose_name="Nombre des journées perdues divisé par nombre d'heures travaillées"
    )
    nombre_incapacites_permanentes_français = models.IntegerField(
        help_text="Nombre d'incapacités permanentes (partielles et totales) notifiées à l'entreprise au cours de l'année considérée (distinguer français et étrangers)"
    )
    nombre_incapacites_permanentes_etrangers = models.IntegerField(
        help_text="Nombre d'incapacités permanentes (partielles et totales) notifiées à l'entreprise au cours de l'année considérée (distinguer français et étrangers)"
    )
    nombre_accidents_travail_mortels = models.IntegerField(
        verbose_name="Nombre d'accidents mortels de travail"
    )
    nombre_accidents_trajet_mortels = models.IntegerField(
        verbose_name="Nombre d'accidents mortels de trajet"
    )
    nombre_accidents_trajet_avec_arret_travail = models.IntegerField(
        verbose_name="Nombre d'accidents de trajet ayant entraîné un arrêt de travail"
    )
    nombre_accidents_salaries_temporaires_ou_prestataires = models.IntegerField(
        verbose_name="Nombre d'accidents dont sont victimes les salariés temporaires ou de prestations de services dans l'entreprise"
    )
    taux_cotisation_securite_sociale_accidents_travail = models.IntegerField(
        verbose_name="Taux de la cotisation sécurité sociale d'accidents de travail"
    )
    montant_cotisation_securite_sociale_accidents_travail = models.IntegerField(
        verbose_name="Montant de la cotisation sécurité sociale d'accidents de travail"
    )
    # 1° A - f) ii - Répartition des accidents par éléments matériels
    # Faire référence aux codes de classification des éléments matériels des accidents (arrêté du 10 octobre 1974).
    nombre_accidents_existence_risques_graves = models.IntegerField(
        verbose_name="Nombre d'accidents liés à l'existence de risques grave",
        help_text="Codes 32 à 40",
    )
    nombre_accidents_chutes_dénivellation = models.IntegerField(
        verbose_name="Nombre d'accidents liés à des chutes avec dénivellation",
        help_text="Code 02",
    )
    nombre_accidents_machines = models.IntegerField(
        verbose_name="Nombre d'accidents occasionnés par des machines",
        help_text="A l'exception de ceux liés aux risques ci-dessus, codes 09 à 30",
    )
    nombre_accidents_circulation_manutention_stockage = models.IntegerField(
        verbose_name="Nombre d'accidents de circulation-manutention-stockage",
        help_text="Codes 01,03,04 et 06,07,08",
    )
    nombre_accidents_objets_en_mouvement = models.IntegerField(
        verbose_name="Nombre d'accidents occasionnés par des objets, masses, particules en mouvement accidentel",
        help_text="Code 05",
    )
    nombre_accidents_autres = models.IntegerField(verbose_name="Autres cas")
    # 1° A - f) iii - Maladies professionnelles
    nombre_maladies_professionnelles = models.IntegerField(
        verbose_name="Nombre des maladies professionnelles",
        help_text="Nombre des maladies professionnelles déclarées à la sécurité sociale au cours de l'année",
    )
    denomination_maladies_professionnelles = models.TextField(
        verbose_name="Dénomination des maladies professionnelles",
        help_text="Dénomination des maladies professionnelles déclarées à la sécurité sociale au cours de l'année",
    )
    nombre_salaries_affections_pathologiques = models.IntegerField(
        verbose_name="Nombre de salariés atteints par des affections pathologiques à caractère professionnel",
    )
    caracterisation_affections_pathologiques = models.TextField(
        verbose_name="Caractérisation des affections pathologiques à caractère professionnel",
    )
    nombre_declaration_procedes_travail_dangereux = models.IntegerField(
        verbose_name="Nombre de déclarations par l'employeur de procédés de travail susceptibles de provoquer des maladies professionnelles",
        help_text="En application de l'article L. 461-4 du code de la sécurité sociale",
    )
    # 1° A - f) iv - Dépenses en matière de sécurité
    effectif_forme_securite = models.IntegerField(
        verbose_name="Effectif formé à la sécurité dans l'année",
    )
    montant_depenses_formation_securite = models.IntegerField(
        verbose_name="Montant des dépenses de formation à la sécurité réalisées dans l'entreprise",
    )
    taux_realisation_programme_securite = models.IntegerField(
        verbose_name="Taux de réalisation du programme de sécurité présenté l'année précédente",
    )
    nombre_plans_specifiques_securite = models.IntegerField(
        verbose_name="Nombre de plans spécifiques de sécurité"
    )
    # 1° A - f) v - Durée et aménagement du temps de travail
    horaire_hebdomadaire_moyen_ouvriers_employes = models.IntegerField(
        verbose_name="Horaire hebdomadaire moyen affiché des ouvriers et employés ou catégories assimilées",
        help_text="Il est possible de remplacer cet indicateur par la somme des heures travaillées durant l'année.",
    )
    somme_heures_travaillees_ouvriers_employes = models.IntegerField(
        verbose_name="Somme des heures travaillées durant l'année par les ouvriers et employés ou catégories assimilées",
    )
    nombre_salaries_repos_compensateur_code_travail = models.IntegerField(
        verbose_name="Nombre de salariés ayant bénéficié d'un repos compensateur au titre du code du travail",
        help_text="Au sens des dispositions du code du travail et du code rural et de la pêche maritime instituant un repos compensateur en matière d'heures supplémentaires.",
    )
    nombre_salaries_repos_compensateur_regime_conventionne = models.IntegerField(
        verbose_name="Nombre de salariés ayant bénéficié d'un repos compensateur au titre d'un régime conventionne",
    )
    nombre_salaries_horaires_individualises = models.IntegerField(
        verbose_name="Nombre de salariés bénéficiant d'un système d'horaires individualisés",
        help_text="Au sens de l'article L. 3121-48.",
    )
    nombre_salaries_temps_partiel_20_30_heures = models.IntegerField(
        verbose_name="Nombre de salariés employés à temps partiel entre 20 et 30 heures (33)",
        help_text="Au sens de l'article L. 3123-1.",
    )
    nombre_salaries_temps_partiel_autres = models.IntegerField(
        verbose_name="Autres formes de temps partiel",
    )
    nombre_salaries_2_jours_repos_hebdomadaire_consecutifs = models.IntegerField(
        verbose_name="Nombre de salariés ayant bénéficié tout au long de l'année considérée de deux jours de repos hebdomadaire consécutifs",
    )
    nombre_moyen_jours_conges_annuels = models.IntegerField(
        verbose_name="Nombre moyen de jours de congés annuels (non compris le repos compensateur)",
        help_text="Repos compensateur non compris. Cet indicateur peut être calculé sur la dernière période de référence.",
    )
    nombre_jours_feries_payes = models.IntegerField(
        verbose_name="Nombre de jours fériés payés",
        help_text="Préciser, le cas échéant, les conditions restrictives.",
    )
    conditions_restrictives_jours_feries_payes = models.TextField()
    # 1° A - f) vi - Absentéisme
    # Possibilités de comptabiliser tous les indicateurs de la rubrique absentéisme, au choix, en journées, 1/2 journées ou heures.
    UNITE_ABESENTEISME_CHOICES = [
        ("J", "Journées"),
        ("1/2J", "1/2 journées"),
        ("H", "Heures"),
    ]
    unite_absenteisme = models.CharField(
        max_length=10,
        choices=UNITE_ABESENTEISME_CHOICES,
    )
    nombre_unites_absence = models.IntegerField(
        verbose_name="Nombre de journées d'absence",
        help_text="Ne sont pas comptés parmi les absences : les diverses sortes de congés, les conflits et le service national.",
    )
    nombre_unites_theoriques_travaillees = models.IntegerField(
        verbose_name="Nombre de journées théoriques travaillées",
    )
    nombre_unites_absence_maladie = models.IntegerField(
        verbose_name="Nombre de journées d'absence pour maladie",
    )
    nombre_unites_absence_duree_1 = models.IntegerField(
        verbose_name="Répartition des absences pour maladie selon leur durée",
        help_text="Les tranches choisies sont laissées au choix des entreprises.",
    )
    nombre_unites_absence_duree_2 = models.IntegerField(
        verbose_name="Répartition des absences pour maladie selon leur durée",
        help_text="Les tranches choisies sont laissées au choix des entreprises.",
    )
    nombre_unites_absence_accidents = models.IntegerField(
        verbose_name="Nombre de journées d'absence pour accidents du travail et de trajet ou maladies professionnelles",
    )
    nombre_unites_absence_maternite = models.IntegerField(
        verbose_name="Nombre de journées d'absence pour maternité",
    )
    nombre_unites_absence_conges_autorises = models.IntegerField(
        verbose_name="Nombre de journées d'absence pour congés autorisés",
        help_text="(événements familiaux, congés spéciaux pour les femmes …)",
    )
    nombre_unites_absence_autres = models.IntegerField(
        verbose_name="Nombre de journées d'absence imputables à d'autres causes",
    )
    # 1° A - f) vii - Organisation et contenu du travail
    nombre_personnes_horaires_alternant_ou_nuit = models.IntegerField(
        verbose_name="Nombre de personnes occupant des emplois à horaires alternant ou de nuit",
    )
    nombre_personnes_horaires_alternant_ou_nuit_50_ans = models.IntegerField(
        verbose_name="Nombre de personnes occupant des emplois à horaires alternant ou de nuit de plus de cinquante ans",
    )
    nombre_hommes_taches_repetitives = models.IntegerField(
        verbose_name="Nombre de salariés homme affectés à des tâches répétitives",
        help_text="Au sens de l'article D. 4163-2",
    )
    nombre_femmes_taches_repetitives = models.IntegerField(
        verbose_name="Nombre de salariés femme affectés à des tâches répétitives",
        help_text="Au sens de l'article D. 4163-2",
    )
    # 1° A - f) viii - Conditions physiques de travail
    nombre_personnes_exposees_bruit = models.IntegerField(
        verbose_name="Nombre de personnes exposées de façon habituelle et régulière à plus de 80 à 85 db à leur poste de travail",
        help_text="Les valeurs limites d'exposition et les valeurs d'exposition déclenchant une action de prévention qui sont fixées dans le tableau prévu à l'article R. 4431-2.",
    )
    nombre_salaries_exposes_temperatures = models.IntegerField(
        verbose_name="Nombre de salariés exposés au froid et à la chaleur",
        help_text="Au sens des articles R. 4223-13 à R. 4223-15",
    )
    nombre_salaries_exposes_temperatures_extremes = models.IntegerField(
        verbose_name="Nombre de salariés exposés aux températures extrêmes",
        help_text="Au sens de l'article D. 4163-2 : température inférieure ou égale à 5 degrés Celsius ou au moins égale à 30 degrés Celsius pour minimum 900 heures par an.",
    )
    nombre_salaries_exposes_intemperies = models.IntegerField(
        verbose_name="Nombre de salariés travaillant aux intempéries de façon habituelle et régulière",
        help_text="Au sens de l'article L. 5424-8 : Sont considérées comme intempéries, les conditions atmosphériques et les inondations lorsqu'elles rendent dangereux ou impossible l'accomplissement du travail eu égard soit à la santé ou à la sécurité des salariés, soit à la nature ou à la technique du travail à accomplir.",
    )
    nombre_produits_toxiques = models.IntegerField(
        verbose_name="Nombre de prélèvements, d'analyses de produits toxiques et mesures",
        help_text="Renseignements tirés du rapport du directeur du service de prévention et de santé au travail interentreprises",
    )
    # 1° A - f) ix - Transformation de l’organisation du travail
    experiences_transformation_organisation_travail = models.TextField(
        verbose_name="Expériences de transformation de l'organisation du travail en vue d'en améliorer le contenu",
        help_text="Pour l'explication de ces expériences d'amélioration du contenu du travail, donner le nombre de salariés concernés.",
    )
    # 1° A - f) x - Dépenses d’amélioration de conditions de travail
    montant_depenses_amelioration_conditions_travail = models.IntegerField(
        verbose_name="Montant des dépenses consacrées à l'amélioration des conditions de travail dans l'entreprise",
        help_text="Non compris l'évaluation des dépenses en matière de santé et de sécurité.",
    )
    taux_realisation_programme_amelioration_conditions_travail = models.IntegerField(
        verbose_name="Taux de réalisation du programme d'amélioration des conditions de travail dans l'entreprise l'année précédente",
    )
    # 1° A - f) xi - Médecine du travail
    # Renseignements tirés du rapport du directeur du service de prévention et de santé au travail interentreprises.
    nombre_visites_medicales_suivi_droit_commun = models.IntegerField(
        verbose_name="Nombre de visites d'information et de prévention des travailleurs en suivi de droit commun",
    )
    nombre_visites_medicales_suivi_individuel = models.IntegerField(
        verbose_name="Nombre de visites d'information et de prévention des travailleurs en suivi individuel renforcé",
    )
    nombre_examens_medicaux_suivi_droit_commun = models.IntegerField(
        verbose_name="Nombre d'examens médicaux des travailleurs en suivi de droit commun",
    )
    nombre_examens_medicaux_suivi_individuel = models.IntegerField(
        verbose_name="Nombre d'examens médicaux des travailleurs en suivi individuel renforcé",
    )
    nombre_examens_complementaires_sous_surveillance = models.IntegerField(
        verbose_name="Nombre d'examens complémentaires des travailleurs soumis à surveillance",
    )
    nombre_examens_complementaires_autres = models.IntegerField(
        verbose_name="Nombre d'examens complémentaires des autres travailleurs",
    )
    pourcentage_temps_medecin_du_travail_analyse = models.IntegerField(
        verbose_name="Part du temps consacré par le médecin du travail à l'analyse",
    )
    pourcentage_temps_medecin_du_travail_intervention = models.IntegerField(
        verbose_name="Part du temps consacré par le médecin du travail à l'intervention en milieu de travail",
    )
    # 1° A - f) xii - Travailleurs inaptes
    nombre_salaries_inaptes = models.IntegerField(
        verbose_name="Nombre de salariés inaptes",
        help_text="Nombre de salariés déclarés définitivement inaptes à leur emploi par le médecin du travail",
    )
    nombre_salaries_reclasses = models.IntegerField(
        verbose_name="Nombre de salariés reclassés",
        help_text="Nombre de salariés reclassés dans l'entreprise à la suite d'une inaptitude",
    )
    # 1° B - Investissement matériel et immatériel
    # 1° B - a) Evolution des actifs nets d’amortissement et de dépréciations éventuelles (immobilisations)
    evolution_amortissement = models.TextField(
        verbose_name="Evolution des actifs nets d’amortissement et de dépréciations éventuelles (immobilisations)",
    )
    # 1° B - b) Le cas échéant, dépenses de recherche et développement
    montant_depenses_recherche_developpement = models.IntegerField(
        verbose_name="Dépenses de recherche et développement",
    )
    # 1° B - c) L’évolution de la productivité et le taux d’utilisation des capacités de production, lorsque ces éléments sont mesurables dans l’entreprise
    evolution_productivite = models.TextField(
        verbose_name="Evolution de la productivité et le taux d’utilisation des capacités de production",
        help_text="lorsque ces éléments sont mesurables dans l’entreprise",
    )

    ###########################################################

    # 2° Egalité professionnelle entre les femmes et les hommes au sein de l'entreprise
    #   I. Indicateurs sur la situation comparée des femmes et des hommes dans l'entreprise
    #     A-Conditions générales d'emploi
    #       a) Effectifs : Données chiffrées par sexe
    nombre_categorie_professionelle_1_en_CDI = models.IntegerField()
    nombre_categorie_professionelle_2_en_CDI = models.IntegerField()
    nombre_categorie_professionelle_1_en_CDD = models.IntegerField()
    nombre_categorie_professionelle_2_en_CDD = models.IntegerField()

    #       b) Durée et organisation du travail: Données chiffrées par sexe
    effectif_temps_complet_homme = models.IntegerField(
        help_text="Effectif à temps complet"
    )
    effectif_temps_complet_femme = models.IntegerField(
        help_text="Effectif à temps complet"
    )
    effectif_temps_partiel_20_30_heures_homme = models.IntegerField(
        help_text="Effectif à temps partiel (compris entre 20 et 30 heures)"
    )
    effectif_temps_partiel_20_30_heures_femme = models.IntegerField(
        help_text="Effectif à temps partiel (compris entre 20 et 30 heures)"
    )

    effectif_temps_partiel_autre_homme = models.IntegerField(
        help_text="Effectif à temps partiel (non compris entre 20 et 30 heures)"
    )
    effectif_temps_partiel_autre_femme = models.IntegerField(
        help_text="Effectif à temps partiel (non compris entre 20 et 30 heures)"
    )
    effectif_travail_poste_homme = models.IntegerField(
        help_text="Effectif en travail posté"
    )
    effectif_travail_poste_femme = models.IntegerField(
        help_text="Effectif en travail posté"
    )
    effectif_travail_nuit_homme = models.IntegerField(
        help_text="Effectif en travail de nuit"
    )
    effectif_travail_nuit_femme = models.IntegerField(
        help_text="Effectif en travail de nuit"
    )
    effectif_horaires_variables_homme = models.IntegerField(
        help_text="Effectif en horaires variables"
    )
    effectif_horaires_variables_femme = models.IntegerField(
        help_text="Effectif en horaires variables"
    )
    effectif_travail_atypique_homme = models.IntegerField(
        help_text="Effectif en travail atypique dont travail durant le week-end"
    )
    effectif_travail_atypique_femme = models.IntegerField(
        help_text="Effectif en travail atypique dont travail durant le week-end"
    )
    #       c) Données sur les congés
    conges_homme_categorie_professionelle_1 = models.IntegerField()
    conges_homme_categorie_professionelle_2 = models.IntegerField()
    conges_femme_categorie_professionelle_1 = models.IntegerField()
    conges_femme_categorie_professionelle_2 = models.IntegerField()
    effectif_homme_conges_compte_epargne_temps = models.IntegerField(
        help_text="La durée du congé doit être supérieure à six mois"
    )
    effectif_homme_conges_parental = models.IntegerField(
        help_text="La durée du congé doit être supérieure à six mois"
    )
    effectif_homme_conges_sabbatique = models.IntegerField(
        help_text="La durée du congé doit être supérieure à six mois"
    )
    effectif_femme_conges_compte_epargne_temps = models.IntegerField(
        help_text="La durée du congé doit être supérieure à six mois"
    )
    effectif_femme_conges_parental = models.IntegerField(
        help_text="La durée du congé doit être supérieure à six mois"
    )
    effectif_femme_congés_sabbatique = models.IntegerField(
        help_text="La durée du congé doit être supérieure à six mois"
    )
    #      d) Données sur les embauches et les départs
    embauches_homme_ouvrier_CDI = models.IntegerField()
    embauches_homme_ouvrier_CDD = models.IntegerField()
    embauches_homme_employe_CDI = models.IntegerField()
    embauches_homme_employe_CDD = models.IntegerField()
    embauches_femme_ouvrier_CDI = models.IntegerField()
    embauches_femme_ouvrier_CDD = models.IntegerField()
    embauches_femme_employe_CDI = models.IntegerField()
    embauches_femme_employe_CDD = models.IntegerField()
    departs_homme_ouvrier_retraite = models.IntegerField()
    departs_homme_ouvrier_demission = models.IntegerField()
    departs_homme_ouvrier_fin_CDD = models.IntegerField()
    departs_homme_ouvrier_licenciement = models.IntegerField()
    departs_homme_employe_retraite = models.IntegerField()
    departs_homme_employe_demission = models.IntegerField()
    departs_homme_employe_fin_CDD = models.IntegerField()
    departs_homme_employe_licenciement = models.IntegerField()
    departs_femme_ouvrier_retraite = models.IntegerField()
    departs_femme_ouvrier_demission = models.IntegerField()
    departs_femme_ouvrier_fin_CDD = models.IntegerField()
    departs_femme_ouvrier_licenciement = models.IntegerField()
    departs_femme_employe_retraite = models.IntegerField()
    departs_femme_employe_demission = models.IntegerField()
    departs_femme_employe_fin_CDD = models.IntegerField()
    departs_femme_employe_licenciement = models.IntegerField()

    #      e) Positionnement dans l'entreprise
    effectif_homme_ouvrier = models.IntegerField()
    effectif_homme_employe = models.IntegerField()
    effectif_femme_ouvrier = models.IntegerField()
    effectif_femme_employe = models.IntegerField()
    effectif_homme_niveau_1 = models.IntegerField()
    effectif_homme_niveau_2 = models.IntegerField()
    effectif_femme_niveau_1 = models.IntegerField()
    effectif_femme_niveau_2 = models.IntegerField()

    #     B - Rémunérations et déroulement de carrière
    #        a) Promotion
    nombre_homme_promotion_ouvrier = models.IntegerField()
    nombre_homme_promotion_employe = models.IntegerField()
    nombre_femme_promotion_ouvrier = models.IntegerField()
    nombre_femme_promotion_employe = models.IntegerField()
    duree_moyenne_entre_deux_promotions_homme = models.IntegerField()
    duree_moyenne_entre_deux_promotions_femme = models.IntegerField()

    #        b) Ancienneté
    anciennete_moyenne_homme_ouvrier = models.IntegerField()
    anciennete_moyenne_homme_employe = models.IntegerField()
    anciennete_moyenne_femme_ouvrier = models.IntegerField()
    anciennete_moyenne_femme_employe = models.IntegerField()
    anciennete_moyenne_homme_dans_ouvrier = models.IntegerField()
    anciennete_moyenne_homme_dans_employe = models.IntegerField()
    anciennete_moyenne_femme_dans_ouvrier = models.IntegerField()
    anciennete_moyenne_femme_dans_employe = models.IntegerField()
    anciennete_moyenne_homme_niveau_1 = models.IntegerField()
    anciennete_moyenne_homme_niveau_2 = models.IntegerField()
    anciennete_moyenne_femme_niveau_1 = models.IntegerField()
    anciennete_moyenne_femme_niveau_2 = models.IntegerField()
    anciennete_moyenne_homme_dans_niveau_1 = models.IntegerField()
    anciennete_moyenne_homme_dans_niveau_2 = models.IntegerField()
    anciennete_moyenne_femme_dans_niveau_1 = models.IntegerField()
    anciennete_moyenne_femme_dans_niveau_2 = models.IntegerField()

    #        c) Age
    age_moyen_homme_ouvrier = models.IntegerField()
    age_moyen_homme_employe = models.IntegerField()
    age_moyen_femme_ouvrier = models.IntegerField()
    age_moyen_femme_employe = models.IntegerField()
    age_moyen_homme_niveau_1 = models.IntegerField()
    age_moyen_homme_niveau_2 = models.IntegerField()
    age_moyen_femme_niveau_1 = models.IntegerField()
    age_moyen_femme_niveau_2 = models.IntegerField()

    #        d) Rémunérations
    remuneration_moyenne_homme_ouvrier = models.IntegerField()
    remuneration_moyenne_homme_employe = models.IntegerField()
    remuneration_moyenne_femme_ouvrier = models.IntegerField()
    remuneration_moyenne_femme_employe = models.IntegerField()
    remuneration_moyenne_homme_niveau_1 = models.IntegerField(
        help_text="Cet indicateur n'a pas à être renseigné lorsque sa mention est de nature à porter atteinte à la confidentialité des données correspondantes, compte tenu notamment du nombre réduit d'individus dans un niveau ou coefficient hiérarchique."
    )
    remuneration_moyenne_homme_niveau_2 = models.IntegerField(
        help_text="Cet indicateur n'a pas à être renseigné lorsque sa mention est de nature à porter atteinte à la confidentialité des données correspondantes, compte tenu notamment du nombre réduit d'individus dans un niveau ou coefficient hiérarchique."
    )
    remuneration_moyenne_femme_niveau_1 = models.IntegerField(
        help_text="Cet indicateur n'a pas à être renseigné lorsque sa mention est de nature à porter atteinte à la confidentialité des données correspondantes, compte tenu notamment du nombre réduit d'individus dans un niveau ou coefficient hiérarchique."
    )
    remuneration_moyenne_femme_niveau_2 = models.IntegerField(
        help_text="Cet indicateur n'a pas à être renseigné lorsque sa mention est de nature à porter atteinte à la confidentialité des données correspondantes, compte tenu notamment du nombre réduit d'individus dans un niveau ou coefficient hiérarchique."
    )

    #     C - Formation
    nombre_moyen_heures_formation_homme_categorie_1 = models.IntegerField(
        help_text="nombre moyen d'heures d'actions de formation par salarié et par an"
    )
    nombre_moyen_heures_formation_homme_categorie_2 = models.IntegerField(
        help_text="nombre moyen d'heures d'actions de formation par salarié et par an"
    )
    nombre_moyen_heures_formation_femme_categorie_1 = models.IntegerField(
        help_text="nombre moyen d'heures d'actions de formation par salarié et par an"
    )
    nombre_moyen_heures_formation_femme_categorie_2 = models.IntegerField(
        help_text="nombre moyen d'heures d'actions de formation par salarié et par an"
    )
    action_adaptation_au_poste_homme_categorie_1 = models.IntegerField()
    action_maintien_emploi_homme_categorie_1 = models.IntegerField(
        help_text="Action : maintien dans l'emploi"
    )
    action_developpement_competences_homme_categorie_1 = models.IntegerField(
        help_text="Action : développement des compétences"
    )
    action_adaptation_au_poste_homme_categorie_2 = models.IntegerField()
    action_maintien_emploi_homme_categorie_2 = models.IntegerField(
        help_text="Action : maintien dans l'emploi"
    )
    action_developpement_competences_homme_categorie_2 = models.IntegerField(
        help_text="Action : développement des compétences"
    )
    action_adaptation_au_poste_femme_categorie_1 = models.IntegerField()
    action_maintien_emploi_homme_categorie_1 = models.IntegerField(
        help_text="Action : maintien dans l'emploi"
    )
    action_developpement_competences_femme_categorie_1 = models.IntegerField(
        help_text="Action : développement des compétences"
    )
    action_adaptation_au_poste_femme_categorie_2 = models.IntegerField()
    action_maintien_emploi_femme_categorie_2 = models.IntegerField(
        help_text="Action : maintien dans l'emploi"
    )
    action_developpement_competences_femme_categorie_2 = models.IntegerField(
        help_text="Action : développement des compétences"
    )

    #     D - Conditions de travail, santé et sécurité au travail
    poste_de_travail_1_homme_risque_pro_1_non_penible = models.IntegerField()
    poste_de_travail_1_homme_risque_pro_1_penible = models.IntegerField()
    poste_de_travail_1_homme_risque_pro_1_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_1_homme_risque_pro_2_non_penible = models.IntegerField()
    poste_de_travail_1_homme_risque_pro_2_penible = models.IntegerField()
    poste_de_travail_1_homme_risque_pro_2_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_1_femme_risque_pro_1_non_penible = models.IntegerField()
    poste_de_travail_1_femme_risque_pro_1_penible = models.IntegerField()
    poste_de_travail_1_femme_risque_pro_1_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_1_femme_risque_pro_2_non_penible = models.IntegerField()
    poste_de_travail_1_femme_risque_pro_2_penible = models.IntegerField()
    poste_de_travail_1_femme_risque_pro_2_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_2_homme_risque_pro_1_non_penible = models.IntegerField()
    poste_de_travail_2_homme_risque_pro_1_penible = models.IntegerField()
    poste_de_travail_2_homme_risque_pro_1_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_2_homme_risque_pro_2_non_penible = models.IntegerField()
    poste_de_travail_2_homme_risque_pro_2_penible = models.IntegerField()
    poste_de_travail_2_homme_risque_pro_2_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_2_femme_risque_pro_1_non_penible = models.IntegerField()
    poste_de_travail_2_femme_risque_pro_1_penible = models.IntegerField()
    poste_de_travail_2_femme_risque_pro_1_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    poste_de_travail_2_femme_risque_pro_2_non_penible = models.IntegerField()
    poste_de_travail_2_femme_risque_pro_2_penible = models.IntegerField()
    poste_de_travail_2_femme_risque_pro_2_penible_repetitif = models.IntegerField(
        help_text="pénibilité incluant le caractère répétitif des tâches"
    )
    accident_travail_homme = models.IntegerField(
        help_text="accidents de travail, accidents de trajet et maladies professionnelles"
    )
    accident_travail_femme = models.IntegerField(
        help_text="accidents de travail, accidents de trajet et maladies professionnelles"
    )
    nombre_accidents_travail_avec_arret_homme = models.IntegerField(
        help_text="Nombre d'accidents de travail ayant entraîné un arrêt de travail"
    )
    nombre_accidents_travail_avec_arret_femme = models.IntegerField(
        help_text="Nombre d'accidents de travail ayant entraîné un arrêt de travail"
    )
    nombre_accidents_trajet_avec_arret_homme = models.IntegerField(
        help_text="Nombre d'accidents de trajet ayant entraîné un arrêt de travail"
    )
    nombre_accidents_trajet_avec_arret_femme = models.IntegerField(
        help_text="Nombre d'accidents de trajet ayant entraîné un arrêt de travail"
    )

    nombre_accidents_riques_graves_homme = models.IntegerField(
        help_text="Nombre d'accidents liés à l'existence de risques graves-codes 32 à 40"
    )
    nombre_accidents_riques_graves_femme = models.IntegerField(
        help_text="Nombre d'accidents liés à l'existence de risques graves-codes 32 à 40"
    )
    nombre_accidents_chutes_denivellation_homme = models.IntegerField(
        help_text="Nombre d'accidents liés à des chutes avec dénivellation-code 02"
    )
    nombre_accidents_chutes_denivellation_femme = models.IntegerField(
        help_text="Nombre d'accidents liés à des chutes avec dénivellation-code 02"
    )
    nombre_accidents_machines_homme = models.IntegerField(
        help_text="Nombre d'accidents occasionnés par des machines (à l'exception de ceux liés aux risques ci-dessus)-codes 09 à 30"
    )
    nombre_accidents_machines_femme = models.IntegerField(
        help_text="Nombre d'accidents occasionnés par des machines (à l'exception de ceux liés aux risques ci-dessus)-codes 09 à 30"
    )

    nombre_accidents_circulation_manutention_stockage_homme = models.IntegerField(
        help_text="Nombre d'accidents de circulation-manutention-stockage-codes 01,03,04 et 06,07,08 ; Nombre d'accidents occasionnés par des objets, masses, particules en mouvement accidentel-code 05"
    )
    nombre_accidents_circulation_manutention_stockage_femme = models.IntegerField(
        help_text="Nombre d'accidents de circulation-manutention-stockage-codes 01,03,04 et 06,07,08 ; Nombre d'accidents occasionnés par des objets, masses, particules en mouvement accidentel-code 05"
    )
    nombre_accidents_autres_homme = models.IntegerField(
        help_text="Nombre des autres cas d'accidents"
    )
    nombre_accidents_autres_femme = models.IntegerField(
        help_text="Nombre des autres cas d'accidents"
    )

    nombre_maladie_1_homme = models.IntegerField(
        help_text="nombre et dénomination des maladies professionnelles déclarées à la Sécurité sociale au cours de l'année"
    )
    nombre_maladie_1_femme = models.IntegerField(
        help_text="nombre et dénomination des maladies professionnelles déclarées à la Sécurité sociale au cours de l'année"
    )
    nombre_maladie_2_homme = models.IntegerField(
        help_text="nombre et dénomination des maladies professionnelles déclarées à la Sécurité sociale au cours de l'année"
    )
    nombre_maladie_2_femme = models.IntegerField(
        help_text="nombre et dénomination des maladies professionnelles déclarées à la Sécurité sociale au cours de l'année"
    )
    nombre_journees_absence_accident_homme = models.IntegerField(
        help_text="nombre de journée d'absence pour accidents de travail, accidents de trajet ou maladies professionnelles "
    )
    nombre_journees_absence_accident_femme = models.IntegerField(
        help_text="nombre de journée d'absence pour accidents de travail, accidents de trajet ou maladies professionnelles "
    )
    maladies_hommes = models.TextField()
    maladies_femmes = models.TextField()
    nombre_arrets_travail_hommes = models.IntegerField()
    nombre_arrets_travail_femmes = models.IntegerField()
    nombre_journees_absence_hommes = models.IntegerField()
    nombre_journees_absence_femmes = models.IntegerField()

    #   II. Indicateurs relatifs à l'articulation entre l'activité professionnelle et l'exercice de la responsabilité familiale
    #      A. Congés
    complement_salaire_conge = models.BooleanField(
        help_text="Existence d'un complément de salaire versé par l'employeur pour le congé de paternité, le congé de maternité, le congé d'adoption"
    )
    nombre_jours_conges_paternite_pris_ouvrier = models.IntegerField(
        help_text="nombre de jours de congés de paternité pris par le salarié par rapport au nombre de jours de congés théoriques "
    )
    nombre_jours_conges_paternite_pris_employe = models.IntegerField(
        help_text="nombre de jours de congés de paternité pris par le salarié par rapport au nombre de jours de congés théoriques "
    )

    #      B-Organisation du temps de travail dans l'entreprise
    existence_organisation_facilitant_vie_familiale_et_professionnelle = models.BooleanField(
        help_text="Existence de formules d'organisation du travail facilitant l'articulation de la vie familiale et de la vie professionnelle"
    )
    nombre_salaries_temps_partiel_choisi_homme_ouvrier = models.IntegerField(
        help_text="nombre de salariés ayant accédé au temps partiel choisi "
    )
    nombre_salaries_temps_partiel_choisi_homme_employe = models.IntegerField(
        help_text="nombre de salariés ayant accédé au temps partiel choisi "
    )
    nombre_salaries_temps_partiel_choisi_femme_ouvrier = models.IntegerField(
        help_text="nombre de salariés ayant accédé au temps partiel choisi "
    )
    nombre_salaries_temps_partiel_choisi_femme_employe = models.IntegerField(
        help_text="nombre de salariés ayant accédé au temps partiel choisi "
    )
    nombre_salaries_temps_partiel_choisi_ayant_repris_temps_plein_homme_ouvrier = (
        models.IntegerField(
            help_text="nombre de salariés ayant accédé au temps partiel choisi "
        )
    )
    nombre_salaries_temps_partiel_choisi_ayant_repris_temps_plein_homme_employe = (
        models.IntegerField(
            help_text="nombre de salariés ayant accédé au temps partiel choisi "
        )
    )
    nombre_salaries_temps_partiel_choisi_ayant_repris_temps_plein_femme_ouvrier = (
        models.IntegerField(
            help_text="nombre de salariés ayant accédé au temps partiel choisi "
        )
    )
    nombre_salaries_temps_partiel_choisi_ayant_repris_temps_plein_femme_employe = (
        models.IntegerField(
            help_text="nombre de salariés ayant accédé au temps partiel choisi "
        )
    )
    participant_accueil_petite_enfance = models.BooleanField(
        help_text="participation de l'entreprise et du comité social et économique aux modes d'accueil de la petite enfance"
    )
    evolution_depenses_credit_impot_famille = models.BooleanField(
        help_text="évolution des dépenses éligibles au crédit d'impôt famille"
    )

    #  III. Stratégie d'action
    mesures_prises_egalite = models.TextField(
        verbose_name="mesures prises au cours de l'année écoulée en vue d'assurer l'égalité professionnelle",
        help_text="Bilan des actions de l'année écoulée et, le cas échéant, de l'année précédente. Evaluation du niveau de réalisation des objectifs sur la base des indicateurs retenus. Explications sur les actions prévues non réalisées",
    )
    objectifs_progression = models.TextField(
        verbose_name="objectifs de progression pour l'année à venir et indicateurs associés",
        help_text="Définition qualitative et quantitative des mesures permettant de les atteindre conformément à l'article R. 2242-2. Evaluation de leur coût. Echéancier des mesures prévues",
    )

    # 3° Fonds propres, endettement et impôts
    capitaux_propres = models.IntegerField(help_text="Capitaux propres de l'entreprise")
    emprunts_et_dettes_financieres = models.IntegerField(
        help_text="Emprunts et dettes financières dont échéances et charges financières"
    )
    impots_et_taxes = models.IntegerField()

    # 4° Rémunération des salariés et dirigeants, dans l'ensemble de leurs éléments
    #   A-Evolution des rémunérations salariales
    #     a) Frais de personnel
    #       i. Montant des rémunérations

    rapport_masse_salariale_effectif_mensuel = models.IntegerField(
        verbose_name="apport entre la masse salariale annuelle (Masse salariale annuelle totale, au sens de la déclaration annuelle de salaire.) et l'effectif mensuel moyen"
    )
    remuneration_moyenne_decembre = models.IntegerField(
        help_text="rémunération moyenne du mois de décembre (effectif permanent) hors primes à périodicité non mensuelle ― base 35 heures"
    )
    remuneration_mensuelle_moyenne = models.IntegerField()
    part_primes_non_mensuelle = models.IntegerField(
        help_text="part des primes à périodicité non mensuelle dans la déclaration de salaire"
    )
    remunerations_tranche_1 = models.IntegerField()
    remunerations_tranche_2 = models.IntegerField()
    remunerations_tranche_3 = models.IntegerField()
    remunerations_tranche_4 = models.IntegerField()
    remunerations_tranche_5 = models.IntegerField()
    remunerations_tranche_6 = models.IntegerField()

    #       ii. Hiérarchie des rémunérations
    rapport_moyenne_deciles = models.IntegerField(
        help_text="rapport entre la moyenne des rémunérations des 10 % des salariés touchant les rémunérations les plus élevées et celle correspondant au 10 % des salariés touchant les rémunérations les moins élevées"
    )
    rapport_moyenne_cadres_ouvriers = models.IntegerField(
        help_text="rapport entre la moyenne des rémunérations des cadres ou assimilés (y compris cadres supérieurs et dirigeants) et la moyenne des rémunérations des ouvriers non qualifiés ou assimilés. Pour être prises en compte, les catégories concernées doivent comporter au minimum dix salariés."
    )
    montant_10_remunerations_les_plus_eleves = models.IntegerField()

    #       iii. Mode de calcul des rémunérations
    pourcentage_salaries_rendement_primes_individuelles = models.IntegerField(
        verbose_name="Pourcentage des salariés dont le salaire dépend, en tout ou partie, du rendement",
        help_text="primes individuelles",
    )
    pourcentage_salaries_rendement_primes_collectives = models.IntegerField(
        verbose_name="Pourcentage des salariés dont le salaire dépend, en tout ou partie, du rendement",
        help_text="primes collectives",
    )
    pourcentage_ouvriers_employes_payes_au_mois = models.IntegerField(
        verbose_name="Pourcentage des ouvriers et employés payés au mois sur la base de l'horaire affiché",
    )

    #      iv. Charge salariale globale
    #         vide

    #   b) Pour les entreprises soumises aux dispositions de l'article L. 225-115 du code de commerce, montant global des rémunérations visées au 4° de cet article
    #      vide

    # B. Epargne salariale : intéressement, participation
