import datetime
from enum import Enum
from functools import partial
from itertools import chain

from django import forms
from django.conf import settings
from django.db import models

from entreprises.models import Entreprise
from utils.models import TimestampedModel


def derniere_annee_a_remplir_index_egapro():
    annee = datetime.date.today().year
    return annee - 1


def prochaine_echeance_index_egapro(derniere_annee_est_publiee: bool) -> datetime.date:
    aujourdhui = datetime.date.today()
    annee = aujourdhui.year
    if derniere_annee_est_publiee:
        return datetime.date(annee + 1, 3, 1)
    else:
        return datetime.date(annee, 3, 1)


def derniere_annee_a_remplir_bdese():
    annee = datetime.date.today().year
    return annee - 1


def annees_a_remplir_bdese():
    annee = datetime.date.today().year
    return [annee - 3, annee - 2, annee - 1, annee, annee + 1, annee + 2]


class CategoryType(Enum):
    HARD_CODED = 1
    PROFESSIONNELLE = 2
    PROFESSIONNELLE_DETAILLEE = 3
    HIERARCHIQUE = 4


class CategoryField(models.JSONField):
    def __init__(
        self,
        base_field=forms.IntegerField,
        category_type=CategoryType.HARD_CODED,
        categories=None,
        *args,
        **kwargs,
    ):
        self.base_field = base_field
        self.category_type = category_type
        self.categories = categories
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.base_field != forms.IntegerField:
            kwargs["base_field"] = self.base_field
        if self.category_type != CategoryType.HARD_CODED:
            kwargs["category_type"] = self.category_type
        if self.categories:
            kwargs["categories"] = self.categories
        return name, path, args, kwargs

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + (
            "base_field",
            "category_type",
            "categories",
        )

    def formfield(self, **kwargs):
        defaults = {
            "base_field": self.base_field,
            "category_type": self.category_type,
        }
        if self.categories:
            defaults["categories"] = self.categories
        defaults.update(kwargs)
        return super().formfield(**defaults)


class PersonalManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user__isnull=False)


class OfficialManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user__isnull=True)


class AlreadyOfficialError(Exception):
    pass


class BDESEError(Exception):
    pass


class AbstractBDESE(TimestampedModel):
    objects = models.Manager()  # The default manager.
    personals = PersonalManager()
    officials = OfficialManager()

    annee = models.IntegerField()
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    categories_professionnelles = models.JSONField(
        verbose_name="Catégories professionnelles",
        help_text="Une structure de qualification détaillée en trois postes minimum",
        null=True,
        blank=True,
    )
    external_fields = models.JSONField(
        default=list,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.entreprise} {self.annee}"

    @classmethod
    def category_fields(cls):
        return [
            field.name
            for field in cls._meta.get_fields()
            if type(field) == CategoryField
        ]

    def mark_step_as_complete(self, step: int):
        completion_steps = self.completion_steps
        completion_steps[self.STEPS[step]] = True
        self.completion_steps = completion_steps

    def mark_step_as_incomplete(self, step: int):
        completion_steps = self.completion_steps
        completion_steps[self.STEPS[step]] = False
        self.completion_steps = completion_steps

    def step_is_complete(self, step: int):
        return self.completion_steps.get(self.STEPS[step], False)

    @property
    def is_complete(self):
        return all(self.completion_steps.values())

    @property
    def is_bdese_300(self):
        return isinstance(self, BDESE_300)

    @property
    def is_bdese_avec_accord(self):
        return isinstance(self, BDESEAvecAccord)

    def officialize(self):
        if not self.user:
            raise AlreadyOfficialError()
        else:
            # https://docs.djangoproject.com/en/4.1/topics/db/queries/#copying-model-instances
            self.pk = None
            self._state.adding = True
            self.user = None
            self.save()


def bdese_completion_steps_default(steps):
    return partial(dict, [(step_name, False) for step_name in steps.values()])


class BDESEAvecAccord(AbstractBDESE):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "user", "annee"],
                name="uniques_PersonalBDESEAvecAccord",
            ),
            models.UniqueConstraint(
                fields=["entreprise", "annee"],
                name="uniques_OfficialBDESEAvecAccord",
                condition=models.Q(user=None),
            ),
        ]
        verbose_name = "BDESE avec accord d'entreprise"
        verbose_name_plural = "BDESE avec accord d'entreprise"

    is_complete = models.BooleanField(default=False)

    def toggle_completion(self):
        self.is_complete = not self.is_complete

    def mark_step_as_complete(self, step: int):
        raise BDESEError(f"La BDESE n'a pas d'étape {step}")

    def mark_step_as_incomplete(self, step: int):
        raise BDESEError(f"La BDESE n'a pas d'étape {step}")

    def step_is_complete(self, step: int):
        raise BDESEError(f"La BDESE n'a pas d'étape {step}")


def bdese_300_completion_steps_default():
    return {step_name: False for step_name in BDESE_300.STEPS.values()}


class BDESE_300(AbstractBDESE):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "user", "annee"],
                name="uniques_PersonalBDESE_300",
            ),
            models.UniqueConstraint(
                fields=["entreprise", "annee"],
                name="uniques_OfficialBDESE_300",
                condition=models.Q(user=None),
            ),
        ]
        verbose_name = "BDESE plus de 300 salariés"
        verbose_name_plural = "BDESE plus de 300 salariés"

    STEPS = {
        0: "Configuration",
        1: "Investissement social",
        2: "Investissement matériel et immatériel",
        3: "Egalité professionnelle homme/femme",
        4: "Fonds propres, endettement et impôts",
        5: "Rémunérations",
        6: "Représentation du personnel et Activités sociales et culturelles",
        7: "Rémunération des financeurs",
        8: "Flux financiers",
        9: "Partenariats",
        10: "Transferts commerciaux et financiers",
        11: "Environnement",
    }

    completion_steps = CategoryField(
        base_field=models.BooleanField,
        categories=list(STEPS.values()),
        default=bdese_300_completion_steps_default,
    )

    categories_professionnelles_detaillees = models.JSONField(
        verbose_name="Catégories professionnelles détaillées",
        help_text="Une structure de qualification détaillée en cinq postes minimum",
        null=True,
        blank=True,
    )
    niveaux_hierarchiques = models.JSONField(
        verbose_name="Niveaux ou coefficients hiérachiques",
        null=True,
        blank=True,
    )

    @property
    def is_configured(self) -> bool:
        return bool(
            self.categories_professionnelles
            and self.categories_professionnelles_detaillees
            and self.niveaux_hierarchiques
        )

    # Décret no 2022-678 du 26 avril 2022
    # https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000045680845
    # 1° Investissements
    # 1° A - Investissement social
    # 1° A - a) Evolution des effectifs par type de contrat, par âge, par ancienneté
    # 1° A - a) i - Effectif
    effectif_total = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        help_text="Tout salarié inscrit à l’effectif au 31/12 quelle que soit la nature de son contrat de travail",
        null=True,
        blank=True,
    )
    effectif_permanent = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        help_text="Les salariés à temps plein, inscrits à l’effectif pendant toute l’année considérée et titulaires d’un contrat de travail à durée indéterminée.",
        null=True,
        blank=True,
    )
    effectif_cdd = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Effectif CDD",
        help_text="Nombre de salariés titulaires d’un contrat de travail à durée déterminée au 31/12",
        blank=True,
        null=True,
    )
    effectif_mensuel_moyen = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        help_text="Somme des effectifs totaux mensuels divisée par 12 (on entend par effectif total tout salarié inscrit à l’effectif au dernier jour du mois considéré)",
        null=True,
        blank=True,
    )
    effectif_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        null=True,
        blank=True,
    )
    effectif_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        null=True,
        blank=True,
    )
    effectif_age = CategoryField(
        categories=[
            "moins de 30 ans",
            "30 à 39 ans",
            "40 à 49 ans",
            "50 ans et plus",
        ],
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
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Effectif de nationalité française",
        null=True,
        blank=True,
    )
    effectif_nationalite_etrangere = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Effectif de nationalité étrangère",
        null=True,
        blank=True,
    )
    effectif_qualification_detaillee_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Répartition des hommes",
        help_text="Répartition de l'effectif total masculin au 31/12 selon une structure de qualification détaillée",
        null=True,
        blank=True,
    )
    effectif_qualification_detaillee_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Répartition des femmes",
        help_text="Répartition de l'effectif total féminin au 31/12 selon une structure de qualification détaillée",
        null=True,
        blank=True,
    )

    # inutile car on a considété la même structure du qualification pour la qualification détaillée:
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
        category_type=CategoryType.PROFESSIONNELLE,
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
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Total des départs",
        null=True,
        blank=True,
    )
    nombre_demissions = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de démissions",
        null=True,
        blank=True,
    )
    nombre_licenciements_economiques = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de licenciements pour motif économique",
        help_text="dont départs en retraite et préretraite",
        null=True,
        blank=True,
    )
    nombre_licenciements_autres = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de licenciements pour d’autres causes",
        null=True,
        blank=True,
    )
    nombre_fin_cdd = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de fins de contrats de travail à durée déterminée",
        null=True,
        blank=True,
    )
    nombre_fin_periode_essai = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de départs au cours de la période d’essai",
        help_text="à ne remplir que si ces départs sont comptabilisés dans le total des départs",
        null=True,
        blank=True,
    )
    nombre_mutations = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de mutations d’un établissement à un autre",
        null=True,
        blank=True,
    )
    nombre_departs_volontaires_retraite_preretraite = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de départs volontaires en retraite et préretraite",
        help_text="Distinguer les différents systèmes légaux et conventionnels de toute nature",
        null=True,
        blank=True,
    )
    nombre_deces = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
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
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés mis en chômage partiel pendant l’année considérée",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_partiel_indemnisees = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre total d'heures de chômage partiel indemnisées",
        help_text="Y compris les heures indemnisées au titre du chômage total en cas d’arrêt de plus de quatre semaines consécutives",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_partiel_non_indemnisees = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre total d'heures de chômage partiel non indemnisées",
        null=True,
        blank=True,
    )
    nombre_salaries_chomage_intemperies = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés mis en chômage intempéries",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_intemperies_indemnisees = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre total d'heures de chômage intempéries indemnisées",
        null=True,
        blank=True,
    )
    nombre_heures_chomage_intemperies_non_indemnisees = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
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
    evolution_nombre_stagiaires = models.TextField(
        verbose_name="Évolution du nombre de stagiaires",
        null=True,
        blank=True,
    )
    # 1° A - e) Formation professionnelle : investissements en formation, publics concernés
    # 1° A - e) i - Formation professionnelle continue
    # Conformément aux données relatives aux contributions de formation professionnelle de la déclaration sociale nominative.
    pourcentage_masse_salariale_formation_continue = models.FloatField(
        verbose_name="Pourcentage de la masse salariale afférent à la formation continue",
        null=True,
        blank=True,
    )
    montant_formation_continue = CategoryField(
        categories=[
            "formation interne",
            "formation effectuée en application de conventions",
            "versement aux organismes de recouvrement",
            "versement auprès d'organismes agréés",
            "autres",
        ],
        verbose_name="Montant consacré à la formation continue",
        null=True,
        blank=True,
    )
    nombre_stagiaires_formation_continue_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Nombre de stagiaires hommes",
        null=True,
        blank=True,
    )
    nombre_stagiaires_formation_continue_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Nombre de stagiaires femmes",
        null=True,
        blank=True,
    )
    nombre_heures_stage_remunerees_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Nombre d'heures de stage rémunérées pour les hommes",
        null=True,
        blank=True,
    )
    nombre_heures_stage_remunerees_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Nombre d'heures de stage rémunérées pour les femmes",
        null=True,
        blank=True,
    )
    nombre_heures_stage_non_remunerees_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Nombre d'heures de stage non rémunérées pour les hommes",
        null=True,
        blank=True,
    )
    nombre_heures_stage_non_remunerees_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Nombre d'heures de stage non rémunérées pour les femmes",
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
    # 1° A - f) Conditions de travail
    # 1° A - f) i - Accidents du travail et de trajet
    # taux_frequence_accidents_travail = CategoryField(
    #     verbose_name="Taux de fréquence des accidents du travail"
    # )
    # nombre_accidents_travail_par_heure_travaillee = models.IntegerField(
    #     verbose_name="Nombre d'accidents avec arrêts de travail divisé par nombre d'heures travaillées"
    # )
    # taux_gravite_accidents_travail = CategoryField(
    #     verbose_name="Taux de gravité des accidents du travail"
    # )
    # nombre_journees_perdues_par_heure_travaillee = models.IntegerField(
    #     verbose_name="Nombre des journées perdues divisé par nombre d'heures travaillées"
    # )
    nombre_incapacites_permanentes_partielles = CategoryField(
        categories=["français", "étrangers"],
        verbose_name="Nombre d'incapacités permanentes partielles notifiées à l'entreprise au cours de l'année considérée",
        null=True,
        blank=True,
    )
    nombre_incapacites_permanentes_totales = CategoryField(
        categories=["français", "étrangers"],
        verbose_name="Nombre d'incapacités permanentes totales notifiées à l'entreprise au cours de l'année considérée",
        null=True,
        blank=True,
    )
    nombre_accidents_travail_mortels = models.IntegerField(
        verbose_name="Nombre d'accidents mortels de travail",
        null=True,
        blank=True,
    )
    nombre_accidents_trajet_mortels = models.IntegerField(
        verbose_name="Nombre d'accidents mortels de trajet",
        null=True,
        blank=True,
    )
    nombre_accidents_trajet_avec_arret_travail = models.IntegerField(
        verbose_name="Nombre d'accidents de trajet ayant entraîné un arrêt de travail",
        null=True,
        blank=True,
    )
    nombre_accidents_salaries_temporaires_ou_prestataires = models.IntegerField(
        verbose_name="Nombre d'accidents dont sont victimes les salariés temporaires ou de prestations de services dans l'entreprise",
        null=True,
        blank=True,
    )
    taux_cotisation_securite_sociale_accidents_travail = models.FloatField(
        verbose_name="Taux de la cotisation sécurité sociale d'accidents de travail",
        null=True,
        blank=True,
    )
    montant_cotisation_securite_sociale_accidents_travail = models.IntegerField(
        verbose_name="Montant de la cotisation sécurité sociale d'accidents de travail",
        null=True,
        blank=True,
    )

    # 1° A - f) ii - Répartition des accidents par éléments matériels
    # Faire référence aux codes de classification des éléments matériels des accidents (arrêté du 10 octobre 1974).
    nombre_accidents_existence_risques_graves = models.IntegerField(
        verbose_name="Nombre d'accidents liés à l'existence de risques grave",
        help_text="Codes 32 à 40",
        null=True,
        blank=True,
    )
    nombre_accidents_chutes_dénivellation = models.IntegerField(
        verbose_name="Nombre d'accidents liés à des chutes avec dénivellation",
        help_text="Code 02",
        null=True,
        blank=True,
    )
    nombre_accidents_machines = models.IntegerField(
        verbose_name="Nombre d'accidents occasionnés par des machines",
        help_text="À l'exception de ceux liés aux risques ci-dessus, codes 09 à 30",
        null=True,
        blank=True,
    )
    nombre_accidents_circulation_manutention_stockage = models.IntegerField(
        verbose_name="Nombre d'accidents de circulation-manutention-stockage",
        help_text="Codes 01, 03, 04 et 06, 07, 08",
        null=True,
        blank=True,
    )
    nombre_accidents_objets_en_mouvement = models.IntegerField(
        verbose_name="Nombre d'accidents occasionnés par des objets, masses, particules en mouvement accidentel",
        help_text="Code 05",
        null=True,
        blank=True,
    )
    nombre_accidents_autres = models.IntegerField(
        verbose_name="Autres cas",
        null=True,
        blank=True,
    )

    # 1° A - f) iii - Maladies professionnelles
    nombre_maladies_professionnelles = models.IntegerField(
        verbose_name="Nombre des maladies professionnelles",
        help_text="Nombre des maladies professionnelles déclarées à la sécurité sociale au cours de l'année",
        null=True,
        blank=True,
    )
    denomination_maladies_professionnelles = models.TextField(
        verbose_name="Dénomination des maladies professionnelles",
        help_text="Dénomination des maladies professionnelles déclarées à la sécurité sociale au cours de l'année",
        null=True,
        blank=True,
    )
    nombre_salaries_affections_pathologiques = models.IntegerField(
        verbose_name="Nombre de salariés atteints par des affections pathologiques à caractère professionnel",
        null=True,
        blank=True,
    )
    caracterisation_affections_pathologiques = models.TextField(
        verbose_name="Caractérisation des affections pathologiques à caractère professionnel",
        null=True,
        blank=True,
    )
    nombre_declaration_procedes_travail_dangereux = models.IntegerField(
        verbose_name="Nombre de déclarations par l'employeur de procédés de travail susceptibles de provoquer des maladies professionnelles",
        help_text="En application de l'article L. 461-4 du code de la sécurité sociale",
        null=True,
        blank=True,
    )

    #     # 1° A - f) iv - Dépenses en matière de sécurité
    effectif_forme_securite = models.IntegerField(
        verbose_name="Effectif formé à la sécurité dans l'année",
        null=True,
        blank=True,
    )
    montant_depenses_formation_securite = models.IntegerField(
        verbose_name="Montant des dépenses de formation à la sécurité réalisées dans l'entreprise",
        null=True,
        blank=True,
    )
    taux_realisation_programme_securite = models.IntegerField(
        verbose_name="Taux de réalisation du programme de sécurité présenté l'année précédente",
        null=True,
        blank=True,
    )
    nombre_plans_specifiques_securite = models.IntegerField(
        verbose_name="Nombre de plans spécifiques de sécurité",
        null=True,
        blank=True,
    )
    # 1° A - f) v - Durée et aménagement du temps de travail
    horaire_hebdomadaire_moyen = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Horaire hebdomadaire moyen affiché des ouvriers et employés ou catégories assimilées",
        help_text="Il est possible de remplacer cet indicateur par la somme des heures travaillées durant l'année.",
        null=True,
        blank=True,
    )
    nombre_salaries_repos_compensateur_code_travail = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés ayant bénéficié d'un repos compensateur au titre du code du travail",
        help_text="Au sens des dispositions du code du travail et du code rural et de la pêche maritime instituant un repos compensateur en matière d'heures supplémentaires.",
        null=True,
        blank=True,
    )
    nombre_salaries_repos_compensateur_regime_conventionne = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés ayant bénéficié d'un repos compensateur au titre d'un régime conventionne",
        null=True,
        blank=True,
    )
    nombre_salaries_horaires_individualises = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés bénéficiant d'un système d'horaires individualisés",
        help_text="Au sens de l'article L. 3121-48.",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_20_30_heures = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés employés à temps partiel entre 20 et 30 heures (33)",
        help_text="Au sens de l'article L. 3123-1.",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_autres = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés employés sous d'autres formes de temps partiel",
        null=True,
        blank=True,
    )
    nombre_salaries_2_jours_repos_hebdomadaire_consecutifs = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés ayant bénéficié tout au long de l'année considérée de deux jours de repos hebdomadaire consécutifs",
        null=True,
        blank=True,
    )
    nombre_moyen_jours_conges_annuels = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre moyen de jours de congés annuels (non compris le repos compensateur)",
        help_text="Repos compensateur non compris. Cet indicateur peut être calculé sur la dernière période de référence.",
        null=True,
        blank=True,
    )
    nombre_jours_feries_payes = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de jours fériés payés",
        null=True,
        blank=True,
    )
    # 1° A - f) vi - Absentéisme
    # Possibilités de comptabiliser tous les indicateurs de la rubrique absentéisme, au choix, en journées, 1/2 journées ou heures.
    UNITE_ABSENTEISME_CHOICES = [
        ("J", "Journées"),
        ("1/2J", "1/2 journées"),
        ("H", "Heures"),
    ]
    unite_absenteisme = models.CharField(
        verbose_name="Unité choisie pour la catégorie absentéisme",
        help_text="Possibilité de comptabiliser tous les indicateurs de la rubrique absentéisme, au choix, en journées, 1/2 journées ou heures.",
        max_length=10,
        choices=UNITE_ABSENTEISME_CHOICES,
        default="J",
    )
    nombre_unites_absence = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'unités d'absence",
        help_text="Ne sont pas comptés parmi les absences : les diverses sortes de congés, les conflits et le service national.",
        null=True,
        blank=True,
    )
    nombre_unites_theoriques_travaillees = models.IntegerField(
        verbose_name="Nombre d'unités théoriques travaillées",
        null=True,
        blank=True,
    )
    nombre_unites_absence_maladie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'unités d'absence pour maladie",
        null=True,
        blank=True,
    )
    nombre_unites_absence_maladie_par_duree = CategoryField(
        categories=["< 3 jours", "de 3 à 90 jours", "> 90 jours"],
        verbose_name="Répartition des absences pour maladie selon leur durée",
        null=True,
        blank=True,
    )
    nombre_unites_absence_accidents = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'unités d'absence pour accidents du travail et de trajet ou maladies professionnelles",
        null=True,
        blank=True,
    )
    nombre_unites_absence_maternite = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'unités d'absence pour maternité",
        null=True,
        blank=True,
    )
    nombre_unites_absence_conges_autorises = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'unités d'absence pour congés autorisés",
        help_text="(événements familiaux, congés spéciaux pour les femmes …)",
        null=True,
        blank=True,
    )
    nombre_unites_absence_autres = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'unités d'absence imputables à d'autres causes",
        null=True,
        blank=True,
    )
    # 1° A - f) vii - Organisation et contenu du travail
    nombre_personnes_horaires_alternant_ou_nuit = models.IntegerField(
        verbose_name="Nombre de personnes occupant des emplois à horaires alternant ou de nuit",
        null=True,
        blank=True,
    )
    nombre_personnes_horaires_alternant_ou_nuit_50_ans = models.IntegerField(
        verbose_name="Nombre de personnes occupant des emplois à horaires alternant ou de nuit de plus de cinquante ans",
        null=True,
        blank=True,
    )
    nombre_taches_repetitives = CategoryField(
        categories=["hommes", "femmes"],
        verbose_name="Nombre de salarié(e)s affectés à des tâches répétitives",
        help_text="Au sens de l'article D. 4163-2",
        null=True,
        blank=True,
    )
    # 1° A - f) viii - Conditions physiques de travail
    nombre_personnes_exposees_bruit = models.IntegerField(
        verbose_name="Nombre de personnes exposées de façon habituelle et régulière à plus de 80 à 85 db à leur poste de travail",
        help_text="Les valeurs limites d'exposition et les valeurs d'exposition déclenchant une action de prévention qui sont fixées dans le tableau prévu à l'article R. 4431-2.",
        null=True,
        blank=True,
    )
    nombre_salaries_exposes_temperatures = models.IntegerField(
        verbose_name="Nombre de salariés exposés au froid et à la chaleur",
        help_text="Au sens des articles R. 4223-13 à R. 4223-15",
        null=True,
        blank=True,
    )
    nombre_salaries_exposes_temperatures_extremes = models.IntegerField(
        verbose_name="Nombre de salariés exposés aux températures extrêmes",
        help_text="Au sens de l'article D. 4163-2 : température inférieure ou égale à 5 degrés Celsius ou au moins égale à 30 degrés Celsius pour minimum 900 heures par an.",
        null=True,
        blank=True,
    )
    nombre_salaries_exposes_intemperies = models.IntegerField(
        verbose_name="Nombre de salariés travaillant aux intempéries de façon habituelle et régulière",
        help_text="Au sens de l'article L. 5424-8 : Sont considérées comme intempéries, les conditions atmosphériques et les inondations lorsqu'elles rendent dangereux ou impossible l'accomplissement du travail eu égard soit à la santé ou à la sécurité des salariés, soit à la nature ou à la technique du travail à accomplir.",
        null=True,
        blank=True,
    )
    nombre_analyses_produits_toxiques = models.IntegerField(
        verbose_name="Nombre de prélèvements, d'analyses de produits toxiques et mesures",
        help_text="Renseignements tirés du rapport du directeur du service de prévention et de santé au travail interentreprises",
        null=True,
        blank=True,
    )
    # 1° A - f) ix - Transformation de l’organisation du travail
    experiences_transformation_organisation_travail = models.TextField(
        verbose_name="Expériences de transformation de l'organisation du travail en vue d'en améliorer le contenu",
        help_text="Pour l'explication de ces expériences d'amélioration du contenu du travail, donner le nombre de salariés concernés.",
        null=True,
        blank=True,
    )
    # 1° A - f) x - Dépenses d’amélioration de conditions de travail
    montant_depenses_amelioration_conditions_travail = models.IntegerField(
        verbose_name="Montant des dépenses consacrées à l'amélioration des conditions de travail dans l'entreprise",
        help_text="Non compris l'évaluation des dépenses en matière de santé et de sécurité.",
        null=True,
        blank=True,
    )
    taux_realisation_programme_amelioration_conditions_travail = models.IntegerField(
        verbose_name="Taux de réalisation du programme d'amélioration des conditions de travail dans l'entreprise l'année précédente",
        null=True,
        blank=True,
    )
    # 1° A - f) xi - Médecine du travail
    # Renseignements tirés du rapport du directeur du service de prévention et de santé au travail interentreprises.
    nombre_visites_medicales = CategoryField(
        categories=["suivi de droit commun", "suivi individuel renforcé"],
        verbose_name="Nombre de visites d'information et de prévention des travailleurs",
        help_text="Selon le type de suivi",
        null=True,
        blank=True,
    )
    nombre_examens_medicaux = CategoryField(
        categories=["suivi de droit commun", "suivi individuel renforcé"],
        verbose_name="Nombre d'examens médicaux des travailleurs",
        null=True,
        blank=True,
    )
    nombre_examens_medicaux_complementaires = CategoryField(
        categories=["soumis à surveillance", "autres"],
        verbose_name="Nombre d'examens médicaux complémentaires des travailleurs",
        null=True,
        blank=True,
    )
    pourcentage_temps_medecin_du_travail = CategoryField(
        categories=["analyse", "intervention"],
        verbose_name="Part du temps consacré par le médecin du travail en milieu de travail",
        null=True,
        blank=True,
    )
    # 1° A - f) xii - Travailleurs inaptes
    nombre_salaries_inaptes = models.IntegerField(
        verbose_name="Nombre de salariés inaptes",
        help_text="Nombre de salariés déclarés définitivement inaptes à leur emploi par le médecin du travail",
        null=True,
        blank=True,
    )
    nombre_salaries_reclasses = models.IntegerField(
        verbose_name="Nombre de salariés reclassés",
        help_text="Nombre de salariés reclassés dans l'entreprise à la suite d'une inaptitude",
        null=True,
        blank=True,
    )
    # 1° B - Investissement matériel et immatériel
    # 1° B - a) Evolution des actifs nets d’amortissement et de dépréciations éventuelles (immobilisations)
    evolution_amortissement = models.TextField(
        verbose_name="Evolution des actifs nets d’amortissement et de dépréciations éventuelles (immobilisations)",
        null=True,
        blank=True,
    )
    # 1° B - b) Le cas échéant, dépenses de recherche et développement
    montant_depenses_recherche_developpement = models.IntegerField(
        verbose_name="Dépenses de recherche et développement",
        null=True,
        blank=True,
    )
    # 1° B - c) L’évolution de la productivité et le taux d’utilisation des capacités de production, lorsque ces éléments sont mesurables dans l’entreprise
    evolution_productivite = models.TextField(
        verbose_name="Evolution de la productivité et le taux d’utilisation des capacités de production",
        help_text="lorsque ces éléments sont mesurables dans l’entreprise",
        null=True,
        blank=True,
    )

    ###########################################################

    # 2° Egalité professionnelle entre les femmes et les hommes au sein de l'entreprise
    #   I. Indicateurs sur la situation comparée des femmes et des hommes dans l'entreprise
    #     A-Conditions générales d'emploi
    #       a) Effectifs : Données chiffrées par sexe
    nombre_CDI_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes en CDI",
        null=True,
        blank=True,
    )
    nombre_CDI_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes en CDI",
        null=True,
        blank=True,
    )
    nombre_CDD_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes en CDD",
        null=True,
        blank=True,
    )
    nombre_CDD_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes en CDD",
        null=True,
        blank=True,
    )
    #       b) Durée et organisation du travail: Données chiffrées par sexe
    effectif_par_duree_homme = CategoryField(
        categories=[
            "temps complet",
            "temps partiel entre 20 et 30 heures",
            "autres temps partiels",
        ],
        verbose_name="Répartition des effectifs hommes selon la durée du travail",
        null=True,
        blank=True,
    )
    effectif_par_duree_femme = CategoryField(
        categories=[
            "temps complet",
            "temps partiel entre 20 et 30 heures",
            "autres temps partiels",
        ],
        verbose_name="Répartition des effectifs femmes selon la durée du travail",
        null=True,
        blank=True,
    )
    effectif_par_organisation_du_travail_homme = CategoryField(
        categories=[
            "travail posté",
            "travail de nuit",
            "horaires variables",
            "travail atypique dont travail durant le week-end",
        ],
        verbose_name="Répartition des effectifs hommes selon l'organisation du travail",
        null=True,
        blank=True,
    )
    effectif_par_organisation_du_travail_femme = CategoryField(
        categories=[
            "travail posté",
            "travail de nuit",
            "horaires variables",
            "travail atypique dont travail durant le week-end",
        ],
        verbose_name="Répartition des effectifs femmes selon l'organisation du travail",
        null=True,
        blank=True,
    )
    #       c) Données sur les congés
    conges_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Répartition des congés des hommes",
        null=True,
        blank=True,
    )
    conges_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Répartition des congés des femmes",
        null=True,
        blank=True,
    )
    conges_par_type_homme = CategoryField(
        categories=["compte épargne-temps", "congé parental", "congé sabbatique"],
        verbose_name="Répartition des congés des hommes selon le type de congés dont la durée est supérieure à six mois",
        null=True,
        blank=True,
    )
    conges_par_type_femme = CategoryField(
        categories=["compte épargne-temps", "congé parental", "congé sabbatique"],
        verbose_name="Répartition des congés des femmes selon le type de congés dont la durée est supérieure à six mois",
        null=True,
        blank=True,
    )
    #      d) Données sur les embauches et les départs
    embauches_CDI_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Répartition des embauches hommes en CDI par catégorie professionnelle",
        null=True,
        blank=True,
    )
    embauches_CDI_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Répartition des embauches femmes en CDI par catégorie professionnelle",
        null=True,
        blank=True,
    )
    embauches_CDD_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Répartition des embauches hommes en CDD par catégorie professionnelle",
        null=True,
        blank=True,
    )
    embauches_CDD_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Répartition des embauches femmes en CDD par catégorie professionnelle",
        null=True,
        blank=True,
    )
    departs_retraite_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes partis en retraite",
        null=True,
        blank=True,
    )
    departs_demission_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes ayant démissionné",
        null=True,
        blank=True,
    )
    departs_fin_CDD_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes en fin de CDD",
        null=True,
        blank=True,
    )
    departs_licenciement_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes licenciés",
        null=True,
        blank=True,
    )
    departs_retraite_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes parties en retraite",
        null=True,
        blank=True,
    )
    departs_demission_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes ayant démissionné",
        null=True,
        blank=True,
    )
    departs_fin_CDD_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes en fin de CDD",
        null=True,
        blank=True,
    )
    departs_licenciement_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes licenciées",
        null=True,
        blank=True,
    )
    #      e) Positionnement dans l'entreprise
    # répartition des effectifs par catégorie professionnelle : déduisible de a)
    effectif_par_niveau_hierarchique_homme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Répartition des effectifs hommes par niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    effectif_par_niveau_hierarchique_femme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Répartition des effectifs femmes par niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    #     B - Rémunérations et déroulement de carrière
    #        a) Promotion
    nombre_promotions_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de promotions homme",
        null=True,
        blank=True,
    )
    nombre_promotions_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de promotions femme",
        null=True,
        blank=True,
    )
    duree_moyenne_entre_deux_promotions_homme = models.IntegerField(
        verbose_name="Durée moyenne entre deux promotions pour les hommes",
        null=True,
        blank=True,
    )
    duree_moyenne_entre_deux_promotions_femme = models.IntegerField(
        verbose_name="Durée moyenne entre deux promotions pour les femmes",
        null=True,
        blank=True,
    )
    #        b) Ancienneté
    anciennete_moyenne_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Ancienneté moyenne des hommes par catégorie professionnelle",
        null=True,
        blank=True,
    )
    anciennete_moyenne_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Ancienneté moyenne des femmes par catégorie professionnelle",
        null=True,
        blank=True,
    )
    anciennete_moyenne_dans_categorie_profesionnelle_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Ancienneté moyenne des hommes dans chaque catégorie professionnelle",
        null=True,
        blank=True,
    )
    anciennete_moyenne_dans_categorie_profesionnelle_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Ancienneté moyenne des femmes dans chaque catégorie professionnelle",
        null=True,
        blank=True,
    )
    anciennete_moyenne_par_niveau_hierarchique_homme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Ancienneté moyenne des hommes par niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    anciennete_moyenne_par_niveau_hierarchique_femme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Ancienneté moyenne des femmes par niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    anciennete_moyenne_dans_niveau_hierarchique_homme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Ancienneté moyenne des hommes dans chaque niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    anciennete_moyenne_dans_niveau_hierarchique_femme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Ancienneté moyenne des femmes dans chaque niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    #        c) Age
    age_moyen_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Age moyen des hommes par catégorie professionnelle",
        null=True,
        blank=True,
    )
    age_moyen_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Age moyen des femmes par catégorie professionnelle",
        null=True,
        blank=True,
    )
    age_moyen_par_niveau_hierarchique_homme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Age moyen des hommes par niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    age_moyen_par_niveau_hierarchique_femme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Age moyen des femmes par niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    #        d) Rémunérations
    REMUNERATIONS_CHOICES = [
        ("moyenne", "Rémunération moyenne"),
        ("mediane", "Rémunération médiane"),
    ]
    remuneration_moyenne_ou_mediane = models.CharField(
        verbose_name="Rémunération moyenne ou médiane",
        help_text="Les indicateurs suivants peuvent être renseignés au choix en rémunération moyenne ou rémunération médiane",
        max_length=10,
        choices=REMUNERATIONS_CHOICES,
        default="moyenne",
    )
    remuneration_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Rémunération moyenne/médiane mensuelle des hommes par catégorie professionnelle",
        null=True,
        blank=True,
    )
    remuneration_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Rémunération moyenne/médiane mensuelle des femmes par catégorie professionnelle",
        null=True,
        blank=True,
    )
    remuneration_par_niveau_hierarchique_homme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Rémunération moyenne/médiane mensuelle des hommes par niveau ou coefficient hiérarchique",
        help_text="Cet indicateur n'a pas à être renseigné lorsque sa mention est de nature à porter atteinte à la confidentialité des données correspondantes, compte tenu notamment du nombre réduit d'individus dans un niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    remuneration_par_niveau_hierarchique_femme = CategoryField(
        category_type=CategoryType.HIERARCHIQUE,
        verbose_name="Rémunération moyenne/médiane mensuelle des femmes par niveau ou coefficient hiérarchique",
        help_text="Cet indicateur n'a pas à être renseigné lorsque sa mention est de nature à porter atteinte à la confidentialité des données correspondantes, compte tenu notamment du nombre réduit d'individus dans un niveau ou coefficient hiérarchique",
        null=True,
        blank=True,
    )
    remuneration_par_age_homme = CategoryField(
        categories=["moins de 30 ans", "30 à 39 ans", "40 à 49 ans", "50 ans et plus"],
        verbose_name="Rémunération moyenne/mediane mensuelle des hommes par tranche d'âge",
        null=True,
        blank=True,
    )
    remuneration_par_age_femme = CategoryField(
        categories=["moins de 30 ans", "30 à 39 ans", "40 à 49 ans", "50 ans et plus"],
        verbose_name="Rémunération moyenne/médiane mensuelle des femmes par tranche d'âge",
        null=True,
        blank=True,
    )
    nombre_femmes_plus_hautes_remunerations = models.IntegerField(
        verbose_name="Nombre de femmes dans les dix plus hautes rémunérations",
        null=True,
        blank=True,
    )
    #     C - Formation
    nombre_moyen_heures_formation_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre moyen d'heures d'actions de formation par salarié et par an",
        help_text="hommes",
        null=True,
        blank=True,
    )
    nombre_moyen_heures_formation_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre moyen d'heures d'actions de formation par salariée et par an",
        help_text="femmes",
        null=True,
        blank=True,
    )
    action_adaptation_au_poste_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes ayant suivi une formation d'adaptation au poste",
        null=True,
        blank=True,
    )
    action_adaptation_au_poste_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes ayant suivi une formation d'adaptation au poste",
        null=True,
        blank=True,
    )
    action_maintien_emploi_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes ayant suivi une formation pour le maintien dans l'emploi",
        null=True,
        blank=True,
    )
    action_maintien_emploi_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes ayant suivi une formation pour le maintien dans l'emploi",
        null=True,
        blank=True,
    )
    action_developpement_competences_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre d'hommes ayant suivi une formation pour le développement des compétences",
        null=True,
        blank=True,
    )
    action_developpement_competences_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de femmes ayant suivi une formation pour le développement des compétences",
        null=True,
        blank=True,
    )
    #     D - Conditions de travail, santé et sécurité au travail
    exposition_risques_pro_homme = CategoryField(
        categories=[
            "manutentions manuelles de charges",
            "postures pénibles",
            "vibrations mécaniques",
            "agents chimiques dangereux",
            "milieu hyperbare",
            "températures extrêmes",
            "bruit",
            "travail de nuit",
            "travail en équipes successives alternantes",
            "travail répétitif",
        ],
        verbose_name="Répartition des postes de travail exposés à des risques professionnels occupés par des hommes",
        null=True,
        blank=True,
    )
    exposition_risques_pro_femme = CategoryField(
        categories=[
            "manutentions manuelles de charges",
            "postures pénibles",
            "vibrations mécaniques",
            "agents chimiques dangereux",
            "milieu hyperbare",
            "températures extrêmes",
            "bruit",
            "travail de nuit",
            "travail en équipes successives alternantes",
            "travail répétitif",
        ],
        verbose_name="Répartition des postes de travail exposés à des risques professionnels occupés par des femmes",
        null=True,
        blank=True,
    )
    accidents_homme = CategoryField(
        categories=[
            "accidents de travail",
            "accidents de trajet",
            "maladies professionnelles",
        ],
        verbose_name="Accidents de travail, accidents de trajet et maladies professionnelles chez les hommes",
        null=True,
        blank=True,
    )
    accidents_femme = CategoryField(
        categories=[
            "accidents de travail",
            "accidents de trajet",
            "maladies professionnelles",
        ],
        verbose_name="Accidents de travail, accidents de trajet et maladies professionnelles chez les femmes",
        null=True,
        blank=True,
    )
    nombre_accidents_travail_avec_arret_homme = models.IntegerField(
        verbose_name="Nombre d'accidents de travail ayant entraîné un arrêt de travail chez les hommes",
        null=True,
        blank=True,
    )
    nombre_accidents_travail_avec_arret_femme = models.IntegerField(
        verbose_name="Nombre d'accidents de travail ayant entraîné un arrêt de travail chez les femmes",
        null=True,
        blank=True,
    )
    nombre_accidents_trajet_avec_arret_homme = models.IntegerField(
        verbose_name="Nombre d'accidents de trajet ayant entraîné un arrêt de travail chez les hommes",
        null=True,
        blank=True,
    )
    nombre_accidents_trajet_avec_arret_femme = models.IntegerField(
        verbose_name="Nombre d'accidents de trajet ayant entraîné un arrêt de travail chez les hommes",
        null=True,
        blank=True,
    )
    nombre_accidents_par_elements_materiels_homme = models.TextField(
        verbose_name="Répartition des accidents par éléments matériels chez les hommes",
        help_text="Faire référence aux codes de classification des éléments matériels des accidents (arrêté du 10 octobre 1974).",
        null=True,
        blank=True,
    )
    nombre_accidents_par_elements_materiels_femme = models.TextField(
        verbose_name="Répartition des accidents par éléments matériels chez les hommes",
        help_text="Faire référence aux codes de classification des éléments matériels des accidents (arrêté du 10 octobre 1974).",
        null=True,
        blank=True,
    )
    nombre_et_denominations_maladies_pro_homme = models.TextField(
        verbose_name="Nombre et dénomination des maladies professionnelles déclarées à la Sécurité sociale au cours de l'année concernant les hommes",
        null=True,
        blank=True,
    )
    nombre_et_denominations_maladies_pro_femme = models.TextField(
        verbose_name="Nombre et dénomination des maladies professionnelles déclarées à la Sécurité sociale au cours de l'année concernant les femmes",
        null=True,
        blank=True,
    )
    nombre_journees_absence_accident_homme = models.IntegerField(
        verbose_name="Nombre de journée d'absence pour accidents de travail, accidents de trajet ou maladies professionnelles chez les hommes",
        null=True,
        blank=True,
    )
    nombre_journees_absence_accident_femme = models.IntegerField(
        verbose_name="Nombre de journée d'absence pour accidents de travail, accidents de trajet ou maladies professionnelles chez les femmes",
        null=True,
        blank=True,
    )
    maladies_homme = CategoryField(
        categories=["nombre d'arrêts de travail", "nombre de journées d'absence"],
        verbose_name="Maladies chez les hommes",
        null=True,
        blank=True,
    )
    maladies_femme = CategoryField(
        categories=["nombre d'arrêts de travail", "nombre de journées d'absence"],
        verbose_name="Maladies chez les femmes",
        null=True,
        blank=True,
    )
    maladies_avec_examen_de_reprise_homme = CategoryField(
        categories=["nombre d'arrêts de travail", "nombre de journées d'absence"],
        verbose_name="Maladies ayant donné lieu à un examen de reprise du travail chez les hommes",
        help_text="en application du 3° de l'article R. 4624-31",
        null=True,
        blank=True,
    )
    maladies_avec_examen_de_reprise_femme = CategoryField(
        categories=["nombre d'arrêts de travail", "nombre de journées d'absence"],
        verbose_name="Maladies ayant donné lieu à un examen de reprise du travail chez les femmes",
        help_text="en application du 3° de l'article R. 4624-31",
        null=True,
        blank=True,
    )
    #   II. Indicateurs relatifs à l'articulation entre l'activité professionnelle et l'exercice de la responsabilité familiale
    #      A. Congés
    complement_salaire_conge_paternite = models.BooleanField(
        verbose_name="Complément de salaire pour le congé de paternité",
        help_text="Existence d'un complément de salaire versé par l'employeur pour le congé de paternité",
        null=True,
    )
    complement_salaire_conge_maternite = models.BooleanField(
        verbose_name="Complément de salaire pour le congé de maternité",
        help_text="Existence d'un complément de salaire versé par l'employeur pour le congé de maternité",
        null=True,
    )
    complement_salaire_conge_adoption = models.BooleanField(
        verbose_name="Complément de salaire pour le congé d'adoption",
        help_text="Existence d'un complément de salaire versé par l'employeur pour le congé d'adoption",
        null=True,
    )
    nombre_jours_conges_paternite_pris = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Jours de congés parternité",
        help_text="Nombre de jours de congés de paternité pris par le salarié par rapport au nombre de jours de congés théoriques",
        null=True,
        blank=True,
    )
    #      B-Organisation du temps de travail dans l'entreprise
    existence_orga_facilitant_vie_familiale_et_professionnelle = models.TextField(
        verbose_name="Existence de formules d'organisation du travail facilitant l'articulation de la vie familiale et de la vie professionnelle",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_choisi_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés homme ayant accédé au temps partiel choisi",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_choisi_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariées femme ayant accédé au temps partiel choisi",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_choisi_vers_temps_plein_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariés homme à temps partiel choisi ayant repris un travail à temps plein",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_choisi_vers_temps_plein_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Nombre de salariées femme à temps partiel choisi ayant repris un travail à temps plein",
        null=True,
        blank=True,
    )
    participation_accueil_petite_enfance = models.BooleanField(
        verbose_name="Participation de l'entreprise et du comité social et économique aux modes d'accueil de la petite enfance",
        null=True,
    )
    evolution_depenses_credit_impot_famille = models.TextField(
        verbose_name="Evolution des dépenses éligibles au crédit d'impôt famille",
        null=True,
        blank=True,
    )
    #  III. Stratégie d'action
    mesures_prises_egalite = models.TextField(
        verbose_name="Mesures prises au cours de l'année écoulée en vue d'assurer l'égalité professionnelle",
        help_text="Bilan des actions de l'année écoulée et, le cas échéant, de l'année précédente. Evaluation du niveau de réalisation des objectifs sur la base des indicateurs retenus. Explications sur les actions prévues non réalisées",
        null=True,
        blank=True,
    )
    objectifs_progression = models.TextField(
        verbose_name="Objectifs de progression pour l'année à venir et indicateurs associés",
        help_text="Définition qualitative et quantitative des mesures permettant de les atteindre conformément à l'article R. 2242-2. Evaluation de leur coût. Echéancier des mesures prévues",
        null=True,
        blank=True,
    )

    ###########################################################

    # 3° Fonds propres, endettement et impôts
    capitaux_propres = models.IntegerField(
        verbose_name="Capitaux propres de l'entreprise",
        null=True,
        blank=True,
    )
    emprunts_et_dettes_financieres = models.IntegerField(
        verbose_name="Emprunts et dettes financières dont échéances et charges financières",
        null=True,
        blank=True,
    )
    impots_et_taxes = models.IntegerField(
        null=True,
        blank=True,
    )

    # 4° Rémunération des salariés et dirigeants, dans l'ensemble de leurs éléments
    #   A-Evolution des rémunérations salariales
    #     a) Frais de personnel

    frais_personnel = models.IntegerField(
        verbose_name="Frais de personnel, y compris cotisations sociales",
        null=True,
        blank=True,
    )
    evolution_salariale_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        null=True,
        blank=True,
    )
    evolution_salariale_par_sexe = CategoryField(
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )
    salaire_base_minimum_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Salaire de base minimum par catégorie",
        null=True,
        blank=True,
    )
    salaire_base_minimum_par_sexe = CategoryField(
        categories=["homme", "femme"],
        verbose_name="Salaire de base minimum par sexe",
        null=True,
        blank=True,
    )
    salaire_moyen_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Salaire moyen par catégorie",
        null=True,
        blank=True,
    )
    salaire_moyen_par_sexe = CategoryField(
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )
    salaire_median_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Salaire médian par catégorie",
        null=True,
        blank=True,
    )
    salaire_median_par_sexe = CategoryField(
        verbose_name="Salaire médian par sexe",
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )

    #       i. Montant des rémunérations
    rapport_masse_salariale_effectif_mensuel_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Rapport entre la masse salariale annuelle et l'effectif mensuel moyen (hommes)",
        help_text="Masse salariale annuelle totale, au sens de la déclaration annuelle de salaire",
        null=True,
        blank=True,
    )
    rapport_masse_salariale_effectif_mensuel_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Rapport entre la masse salariale annuelle et l'effectif mensuel moyen (femmes)",
        help_text="Masse salariale annuelle totale, au sens de la déclaration annuelle de salaire",
        null=True,
        blank=True,
    )
    remuneration_moyenne_decembre_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Rémunération moyenne du mois de décembre (effectif permanent) hors primes à périodicité non mensuelle (hommes)",
        help_text="base 35 heures",
        null=True,
        blank=True,
    )
    remuneration_moyenne_decembre_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Rémunération moyenne du mois de décembre (effectif permanent) hors primes à périodicité non mensuelle (femmes)",
        help_text="base 35 heures",
        null=True,
        blank=True,
    )
    remuneration_mensuelle_moyenne_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Rémunération mensuelle moyenne (hommes)",
        null=True,
        blank=True,
    )
    remuneration_mensuelle_moyenne_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Rémunération mensuelle moyenne (femmes)",
        null=True,
        blank=True,
    )
    part_primes_non_mensuelle_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Part des primes à périodicité non mensuelle dans la déclaration de salaire (hommes)",
        null=True,
        blank=True,
    )
    part_primes_non_mensuelle_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE_DETAILLEE,
        verbose_name="Part des primes à périodicité non mensuelle dans la déclaration de salaire (femmes)",
        null=True,
        blank=True,
    )
    remunerations = models.TextField(
        verbose_name="Grille des rémunérations",
        help_text="Faire une grille des rémunérations en distinguant au moins six tranches.",
        null=True,
        blank=True,
    )

    #       ii. Hiérarchie des rémunérations
    rapport_moyenne_deciles = models.IntegerField(
        verbose_name="rapport entre la moyenne des rémunérations des 10 % des salariés touchant les rémunérations les plus élevées et celle correspondant au 10 % des salariés touchant les rémunérations les moins élevées",
        null=True,
        blank=True,
    )
    rapport_moyenne_cadres_ouvriers = models.IntegerField(
        verbose_name="Rapport entre la moyenne des rémunérations des cadres ou assimilés (y compris cadres supérieurs et dirigeants) et la moyenne des rémunérations des ouvriers non qualifiés ou assimilés.",
        help_text="Pour être prises en compte, les catégories concernées doivent comporter au minimum dix salariés.",
        null=True,
        blank=True,
    )
    montant_10_remunerations_les_plus_eleves = models.IntegerField(
        verbose_name="Montant global des dix rémunérations les plus élevées.",
        null=True,
        blank=True,
    )

    #       iii. Mode de calcul des rémunérations
    pourcentage_salaries_primes_de_rendement = CategoryField(
        categories=["primes individuelles", "primes collectives"],
        verbose_name="Pourcentage des salariés dont le salaire dépend, en tout ou partie, du rendement",
        null=True,
        blank=True,
    )
    pourcentage_ouvriers_employes_payes_au_mois = models.IntegerField(
        verbose_name="Pourcentage des ouvriers et employés payés au mois sur la base de l'horaire affiché",
        null=True,
        blank=True,
    )  # TODO: remplacer le pourcentage par une valeur absolue ?

    #       iv. Charge salariale globale
    charge_salariale_globale = models.IntegerField(
        null=True,
        blank=True,
    )

    #     b) Pour les entreprises soumises aux dispositions de l'article L. 225-115 du code de commerce, montant global des rémunérations visées au 4° de cet article
    montant_global_hautes_remunerations = models.IntegerField(
        verbose_name="Montant global des hautes rémunérations",
        help_text="Montant global, certifié exact par les commissaires aux comptes, s'il en existe, des rémunérations versées aux personnes les mieux rémunérées, le nombre de ces personnes étant de dix ou de cinq selon que l'effectif du personnel excède ou non deux cents salariés ; uniquement pour les entreprises soumises aux dispositions de l'article L. 225-115 du code de commerce",
        null=True,
        blank=True,
    )

    # B. Epargne salariale : intéressement, participation
    montant_global_reserve_de_participation = models.IntegerField(
        verbose_name="Montant global de la réserve de participation",
        help_text="Le montant global de la réserve de participation est le montant de la réserve dégagée-ou de la provision constituée-au titre de la participation sur les résultats de l'exercice considéré.",
        null=True,
        blank=True,
    )
    montant_moyen_participation = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Montant moyen de la participation et/ ou de l'intéressement par salarié bénéficiaire",
        help_text="La participation est envisagée ici au sens du titre II du livre III de la partie III.",
        null=True,
        blank=True,
    )
    part_capital_detenu_par_salaries = models.IntegerField(
        verbose_name="Part du capital détenu par les salariés (dirigeants exclus) grâce à un système de participation",
        help_text="système de participation : participation aux résultats, intéressement, actionnariat …",
        null=True,
        blank=True,
    )

    # C-Rémunérations accessoires : primes par sexe et par catégorie professionnelle, avantages en nature, régimes de prévoyance et de retraite complémentaire
    avantages_sociaux = models.TextField(
        verbose_name="Avantages sociaux dans l'entreprise : pour chaque avantage préciser le niveau de garantie pour les catégories retenues pour les effectifs",
        null=True,
        blank=True,
    )

    # D-Rémunération des dirigeants mandataires sociaux
    remuneration_dirigeants_mandataires_sociaux = models.IntegerField(
        verbose_name="Rémunération des dirigeants mandataires sociaux",
        null=True,
        blank=True,
    )

    # 5° Représentation du personnel et Activités sociales et culturelles
    #   A-Représentation du personnel
    #     a) Représentants du personnel et délégués syndicaux

    composition_CSE_etablissement = models.TextField(
        verbose_name="Composition des comités sociaux et économiques et/ ou d'établissement avec indication, s'il y a lieu, de l'appartenance syndicale",
        null=True,
        blank=True,
    )
    participation_elections = models.TextField(
        verbose_name="Participation aux élections (par collège) par catégories de représentants du personnel",
        null=True,
        blank=True,
    )
    volume_credit_heures = models.IntegerField(
        verbose_name="Volume global des crédits d'heures utilisés pendant l'année considérée",
        null=True,
        blank=True,
    )
    nombre_reunion_representants_personnel = models.IntegerField(
        verbose_name="Nombre de réunions avec les représentants du personnel et les délégués syndicaux pendant l'année considérée",
        null=True,
        blank=True,
    )
    accords_conclus = models.TextField(
        verbose_name="Dates et signatures et objet des accords conclus dans l'entreprise pendant l'année considérée",
        null=True,
        blank=True,
    )
    nombre_personnes_conge_education_ouvriere = models.IntegerField(
        verbose_name="Nombre de personnes bénéficiaires d'un congé d'éducation ouvrière",
        help_text="Au sens des articles L. 2145-5 et suivants.",
        null=True,
        blank=True,
    )

    #     b) Information et communication
    nombre_heures_reunion_personnel = models.IntegerField(
        verbose_name="Nombre d'heures consacrées aux différentes formes de réunion du personnel",
        help_text="On entend par réunion du personnel, les réunions régulières de concertation, concernant les relations et conditions de travail organisées par l'entreprise.",
        null=True,
        blank=True,
    )
    elements_systeme_accueil = models.TextField(
        verbose_name="Eléments caractéristiques du système d'accueil",
        null=True,
        blank=True,
    )
    elements_systeme_information = models.TextField(
        verbose_name="Eléments caractéristiques du système d'information ascendante ou descendante et niveau d'application",
        null=True,
        blank=True,
    )
    elements_systeme_entretiens_individuels = models.TextField(
        verbose_name="Eléments caractéristiques du système d'entretiens individuels",
        help_text="Préciser leur périodicité.",
        null=True,
        blank=True,
    )
    #     c) Différends concernant l'application du droit du travail
    differends_application_droit_du_travail = models.TextField(
        verbose_name="Différends concernant l'application du droit du travail",
        help_text="Avec indication de la nature du différend et, le cas échéant, de la solution qui y a mis fin.",
        null=True,
        blank=True,
    )
    #   B-Activités sociales et culturelles
    #     a) Activités sociales
    contributions_financement_CSE_CSEE = models.TextField(
        verbose_name="Contributions au financement, le cas échéant, du comité social et économique et des comités sociaux économiques d'établissement",
        null=True,
        blank=True,
    )
    contributions_autres_depenses = CategoryField(
        categories=[
            "logement",
            "transport",
            "restauration",
            "loisirs",
            "vacances",
            "divers",
        ],
        verbose_name="Autres dépenses directement supportées par l'entreprise",
        help_text="Dépenses consolidées de l'entreprise.",
        null=True,
        blank=True,
    )
    #    b) Autres charges sociales
    cout_prestations_maladie_deces = models.IntegerField(
        verbose_name="Coût pour l'entreprise des prestations complémentaires (maladie, décès)",
        help_text="Versements directs ou par l'intermédiaire d'assurances",
        null=True,
        blank=True,
    )
    cout_prestations_vieillesse = models.IntegerField(
        verbose_name="Coût pour l'entreprise des prestations complémentaires (vieillesse)",
        help_text="Versements directs ou par l'intermédiaire d'assurances",
        null=True,
        blank=True,
    )
    equipements_pour_conditions_de_vie = models.TextField(
        verbose_name="Equipements réalisés par l'entreprise et touchant aux conditions de vie des salariés à l'occasion de l'exécution du travail",
        null=True,
        blank=True,
    )

    # 6° Rémunération des financeurs, en dehors des éléments mentionnés au 4°
    #   A-Rémunération des actionnaires (revenus distribués)
    remuneration_actionnaires = models.IntegerField(
        verbose_name="Rémunération des actionnaires (revenus distribués)",
        null=True,
        blank=True,
    )

    #   B-Rémunération de l'actionnariat salarié
    remuneration_actionnariat_salarie = models.IntegerField(
        verbose_name="Rémunération de l'actionnariat salarié (montant des actions détenues dans le cadre de l'épargne salariale, part dans le capital, dividendes reçus)",
        null=True,
        blank=True,
    )

    # 7° Flux financiers à destination de l'entreprise
    #   A-Aides publiques
    aides_financieres = models.TextField(
        verbose_name="Les aides ou avantages financiers consentis à l'entreprise par l'Union européenne, l'Etat, une collectivité territoriale, un de leurs établissements publics ou un organisme privé chargé d'une mission de service public, et leur utilisation",
        help_text="Pour chacune de ces aides, l'employeur indique la nature de l'aide, son objet, son montant, les conditions de versement et d'emploi fixées, le cas échéant, par la personne publique qui l'attribue et son utilisation",
        null=True,
        blank=True,
    )

    #   B-Réductions d'impôts
    reductions_impots = models.IntegerField(
        verbose_name="Réductions d'impôts",
        null=True,
        blank=True,
    )

    #   C-Exonérations et réductions de cotisations sociales
    exonerations_cotisations_sociales = models.IntegerField(
        verbose_name="Exonérations et réductions de cotisations sociales",
        null=True,
        blank=True,
    )

    #   D-Crédits d'impôts
    credits_impots = models.IntegerField(
        verbose_name="Crédits d'impôts",
        null=True,
        blank=True,
    )

    #   E-Mécénat
    mecenat = models.IntegerField(
        verbose_name="Mécénat",
        null=True,
        blank=True,
    )

    #   F-Résultats financiers
    chiffre_affaires = models.IntegerField(
        verbose_name=" Le chiffre d'affaires",
        null=True,
        blank=True,
    )
    benefices_ou_pertes = models.IntegerField(
        verbose_name="Les bénéfices ou pertes constatés",
        null=True,
        blank=True,
    )
    resultats_globaux = CategoryField(
        categories=["valeur", "volume"],
        verbose_name="Les résultats globaux de la production",
        null=True,
        blank=True,
    )
    affectation_benefices = models.TextField(
        verbose_name="L'affectation des bénéfices réalisés",
        null=True,
        blank=True,
    )

    # 8° Partenariats
    #   A-Partenariats conclus pour produire des services ou des produits pour une autre entreprise
    partenariats_pour_produire = models.TextField(
        verbose_name="Partenariats conclus pour produire des services ou des produits pour une autre entreprise",
        null=True,
        blank=True,
    )

    #   B-Partenariats conclus pour bénéficier des services ou des produits d'une autre entreprise
    partenariats_pour_beneficier = models.TextField(
        verbose_name="Partenariats conclus pour bénéficier des services ou des produits d'une autre entreprise",
        null=True,
        blank=True,
    )

    # 9° Pour les entreprises appartenant à un groupe, transferts commerciaux et financiers entre les entités du groupe
    #    A-Transferts de capitaux tels qu'ils figurent dans les comptes individuels des sociétés du groupe lorsqu'ils présentent une importance significative
    transferts_de_capitaux = models.TextField(
        verbose_name="Transferts de capitaux tels qu'ils figurent dans les comptes individuels des sociétés du groupe lorsqu'ils présentent une importance significative",
        null=True,
        blank=True,
    )

    #    B-Cessions, fusions, et acquisitions réalisées
    cessions_fusions_acquisitions = models.TextField(
        verbose_name="Cessions, fusions, et acquisitions réalisées",
        null=True,
        blank=True,
    )

    # 10° Environnement
    #    I-Pour les entreprises soumises à la déclaration prévue à l'article R. 225-105 du code de commerce
    #        A-Politique générale en matière environnementale
    informations_environnementales = models.TextField(
        verbose_name="Informations environnementales présentées en application du 2° du A du II de l'article R. 225-105 du code de commerce",
        null=True,
        blank=True,
    )

    #       B-Economie circulaire
    quantite_de_dechets_dangereux_soumis_DPEF = models.TextField(
        verbose_name="Prévention et gestion de la production de déchets : évaluation de la quantité de déchets dangereux définis à l'article R. 541-8 du code de l'environnement et faisant l'objet d'une émission du bordereau mentionné à l'article R. 541-45 du même code",
        null=True,
        blank=True,
    )

    #     C-Changement climatique
    bilan_gaz_effet_de_serre_soumis_DPEF = models.TextField(
        verbose_name="Bilan des émissions de gaz à effet de serre prévu par l'article L. 229-25 du code de l'environnement ou bilan simplifié prévu par l'article 244 de la loi n° 2020-1721 du 29 décembre 2020 de finances pour 2021 pour les entreprises tenues d'établir ces différents bilans",
        null=True,
        blank=True,
    )

    #    II-Pour les entreprises non soumises à la déclaration prévue à l'article R. 225-105 du code de commerce
    #        A-Politique générale en matière environnementale
    prise_en_compte_questions_environnementales = models.TextField(
        verbose_name="Organisation de l'entreprise pour prendre en compte les questions environnementales et, le cas échéant, les démarches d'évaluation ou de certification en matière d'environnement",
        null=True,
        blank=True,
    )

    #       B-Economie circulaire
    #          i-Prévention et gestion de la production de déchets
    quantite_de_dechets_dangereux_non_soumis_DPEF = models.TextField(
        verbose_name="Évaluation de la quantité de déchets dangereux définis à l'article R. 541-8 du code de l'environnement et faisant l'objet d'une émission du bordereau mentionné à l'article R. 541-45 du même code",
        null=True,
        blank=True,
    )
    #          ii-Utilisation durable des ressources
    consommation_eau = models.IntegerField(
        verbose_name="consommation d'eau",
        null=True,
        blank=True,
    )
    consommation_energie = models.IntegerField(
        verbose_name="consommation d'énergie",
        null=True,
        blank=True,
    )

    #     C-Changement climatique
    #        i-Identification des postes d'émissions directes de gaz à effet de serre
    postes_emissions_directes_gaz_effet_de_serre = models.TextField(
        verbose_name="Identification des postes d'émissions directes de gaz à effet de serre",
        help_text="produites par les sources fixes et mobiles nécessaires aux activités de l'entreprise (communément appelées \"émissions du scope 1\") et, lorsque l'entreprise dispose de cette information, évaluation du volume de ces émissions de gaz à effet de serre ",
        null=True,
        blank=True,
    )

    bilan_gaz_effet_de_serre_non_soumis_DPEF = models.TextField(
        verbose_name="Bilan des émissions de gaz à effet de serre prévu par l'article L. 229-25 du code de l'environnement ou bilan simplifié prévu par l'article 244 de la loi n° 2020-1721 du 29 décembre 2020 de finances pour 2021 pour les entreprises tenues d'établir ces différents bilans",
        null=True,
        blank=True,
    )


def bdese_50_300_completion_steps_default():
    return {step_name: False for step_name in BDESE_50_300.STEPS.values()}


class BDESE_50_300(AbstractBDESE):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "user", "annee"],
                name="uniques_PersonalBDESE_50_300",
            ),
            models.UniqueConstraint(
                fields=["entreprise", "annee"],
                name="uniques_OfficialBDESE_50_300",
                condition=models.Q(user=None),
            ),
        ]
        verbose_name = "BDESE 50 à 300 salariés"
        verbose_name_plural = "BDESE 50 à 300 salariés"

    STEPS = {
        0: "Configuration",
        1: "Investissement social",
        2: "Investissement matériel et immatériel",
        3: "Egalité professionnelle homme/femme",
        4: "Fonds propres, endettement et impôts",
        5: "Rémunérations",
        6: "Représentation du personnel et Activités sociales et culturelles",
        7: "Rémunération des financeurs",
        8: "Flux financiers",
        9: "Partenariats",
        10: "Transferts commerciaux et financiers",
        11: "Environnement",
    }

    completion_steps = CategoryField(
        base_field=models.BooleanField,
        categories=list(STEPS.values()),
        default=bdese_50_300_completion_steps_default,
    )

    @property
    def is_configured(self) -> bool:
        return bool(self.categories_professionnelles)

    # Décret no 2022-678 du 26 avril 2022
    # https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000045680861
    # 1° Investissements
    # 1° A - Investissement social
    # 1° A - a) Evolution des effectifs par type de contrat, par âge, par ancienneté
    effectif_mensuel = CategoryField(
        categories=[
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Aout",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        ],
        help_text="Evolution des effectifs retracée mois par mois",
        null=True,
        blank=True,
    )
    effectif_cdi = models.IntegerField(
        verbose_name="Effectif CDI",
        help_text="Nombre de salariés titulaires d’un contrat de travail à durée indéterminée",
        blank=True,
        null=True,
    )
    effectif_cdd = models.IntegerField(
        verbose_name="Effectif CDD",
        help_text="Nombre de salariés titulaires d’un contrat de travail à durée déterminée",
        blank=True,
        null=True,
    )
    nombre_salaries_temporaires = models.IntegerField(
        verbose_name="Nombre de salariés temporaires",
        null=True,
        blank=True,
    )
    nombre_travailleurs_exterieurs = models.IntegerField(
        verbose_name="Nombre de travailleurs extérieurs",
        help_text="Nombre de salariés appartenant à une entreprise extérieure",
        null=True,
        blank=True,
    )
    nombre_journees_salaries_temporaires = models.IntegerField(
        verbose_name="Nombre de journées de travail réalisées au cours des douze derniers mois par les salariés temporaires",
        null=True,
        blank=True,
    )
    nombre_contrats_insertion_formation_jeunes = models.IntegerField(
        verbose_name="Nombre de contrats d'insertion et de formation en alternance ouverts aux jeunes de moins de vingt-six ans",
        null=True,
        blank=True,
    )
    motifs_contrats_cdd_temporaire_temps_partiel_exterieurs = models.TextField(
        verbose_name="Motifs",
        help_text="Motifs ayant conduit l'entreprise à recourir aux contrats de travail à durée déterminée, aux contrats de travail temporaire, aux contrats de travail à temps partiel, ainsi qu'à des salariés appartenant à une entreprise extérieure",
        null=True,
        blank=True,
    )
    # 1° A - b) Evolution des emplois par catégorie professionnelle
    effectif_homme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        null=True,
        blank=True,
    )
    effectif_femme = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        null=True,
        blank=True,
    )
    actions_prevention_formation = models.TextField(
        verbose_name="Actions de prévention et de formation",
        help_text="Indication des actions de prévention et de formation que l'employeur envisage de mettre en œuvre, notamment au bénéfice des salariés âgés, peu qualifiés ou présentant des difficultés sociales particulières",
        null=True,
        blank=True,
    )
    # 1° A - c) Evolution de l'emploi des personnes handicapées et mesures prises pour le développer
    actions_emploi_personnes_handicapees = models.TextField(
        verbose_name="Actions entreprises ou projetées",
        help_text="Actions entreprises ou projetées en matière d'embauche, d'adaptation, de réadaptation ou de formation professionnelle",
        null=True,
        blank=True,
    )
    # Déclaration annuelle prévue à l'article L. 5212-5 à l'exclusion des informations mentionnées à l'article D. 5212-4 ;
    # TODO: que contient cette déclaration annuelle pour les 50-300 salariés et cela se traduit par combien de champs dans notre formulaire ?
    doeth = models.TextField(
        verbose_name="Déclaration obligatoire d'emploi des travailleurs handicapés",
        help_text="Déclaration annuelle prévue à l'article L. 5212-5 à l'exclusion des informations mentionnées à l'article D. 5212-4",
        null=True,
        blank=True,
    )
    # 1° A - d) Evolution du nombre de stagiaires de plus de 16 ans
    evolution_nombre_stagiaires = models.TextField(
        verbose_name="Évolution du nombre de stagiaires de plus de 16 ans",
        null=True,
        blank=True,
    )
    # 1° A - e) Formation professionnelle : investissements en formation, publics concernés
    orientations_formation_professionnelle = models.TextField(
        verbose_name="Orientations de la formation professionnelle",
        help_text="Les orientations de la formation professionnelle dans l'entreprise telles qu'elles résultent de la consultation prévue à l'article L. 2312-24",
        null=True,
        blank=True,
    )
    resultat_negociations_L_2241_6 = models.TextField(
        verbose_name="Résultat éventuel des négociations prévues à l'article L. 2241-6",
        null=True,
        blank=True,
    )
    conclusions_verifications_L_6361_1_L_6323_13_L_6362_4 = models.TextField(
        verbose_name="Conclusions éventuelles des services de contrôle faisant suite aux vérifications effectuées en application des articles L. 6361-1, L. 6323-13 et L. 6362-4",
        null=True,
        blank=True,
    )
    bilan_actions_plan_formation = models.TextField(
        verbose_name="Bilan des actions comprises dans le plan de formation de l'entreprise",
        help_text="Le bilan des actions comprises dans le plan de formation de l'entreprise pour l'année antérieure et pour l'année en cours comportant la liste des actions de formation, des bilans de compétences et des validations des acquis de l'expérience réalisés, rapportés aux effectifs concernés répartis par catégorie socioprofessionnelle et par sexe",
        null=True,
        blank=True,
    )
    informations_conges_formation = models.TextField(
        verbose_name="Informations relatives aux congés de formation",
        help_text="Les informations, pour l'année antérieure et l'année en cours, relatives aux congés individuels de formation, aux congés de bilan de compétences, aux congés de validation des acquis de l'expérience et aux congés pour enseignement accordés ; notamment leur objet, leur durée et leur coût, aux conditions dans lesquelles ces congés ont été accordés ou reportés ainsi qu'aux résultats obtenus",
        null=True,
        blank=True,
    )
    nombre_salaries_beneficaires_abondement = models.IntegerField(
        verbose_name="Nombre des salariés bénéficiaires de l'abondement mentionné à l'avant-dernier alinéa du II de l'article L. 6315-1",
        null=True,
        blank=True,
    )
    somme_abondement = models.FloatField(
        verbose_name="Sommes versées à ce titre",
        null=True,
        blank=True,
    )
    nombre_salaries_beneficiaires_entretien_professionnel = models.IntegerField(
        verbose_name="Nombre des salariés bénéficiaires de l'entretien professionnel mentionné au I de l'article L. 6315-1.",
        null=True,
        blank=True,
    )
    bilan_contrats_alternance = models.TextField(
        verbose_name="Bilan, pour l'année antérieure et l'année en cours, des conditions de mise en œuvre des contrats d'alternance",
        null=True,
        blank=True,
    )
    emplois_periode_professionnalisation = models.TextField(
        verbose_name="Emplois occupés pendant et à l'issue de leur action ou de leur période de professionnalisation",
        null=True,
        blank=True,
    )
    effectif_periode_professionnalisation_par_age = CategoryField(
        categories=[
            "moins de 30 ans",
            "30 à 39 ans",
            "40 à 49 ans",
            "50 ans et plus",
        ],
        verbose_name="Effectifs intéressés par âge",
        null=True,
        blank=True,
    )
    effectif_periode_professionnalisation_par_sexe = CategoryField(
        categories=["homme", "femme"],
        verbose_name="Effectifs intéressés par sexe",
        null=True,
        blank=True,
    )
    effectif_periode_professionnalisation_par_niveau_initial = CategoryField(
        categories=[
            "niveau I",
            "niveau II",
            "niveau III",
            "niveau IV",
        ],
        verbose_name="Effectifs intéressés par niveau initial de formation",
        null=True,
        blank=True,
    )
    resultats_periode_professionnalisation = models.TextField(
        verbose_name="Résultats obtenus en fin d'action ou de période de professionnalisation ainsi que les conditions d'appréciation et de validation",
        null=True,
        blank=True,
    )
    bilan_cpf = models.TextField(
        verbose_name="Bilan de la mise en œuvre du compte personnel de formation",
        null=True,
        blank=True,
    )
    # 1° A - f) Conditions de travail : durée du travail dont travail à temps partiel et aménagement du temps de travail ; Données sur le travail à temps partiel :
    nombre_salaries_temps_partiel_par_sexe = CategoryField(
        categories=["homme", "femme"],
        verbose_name="Nombre de salariés travaillant à temps partiel",
        null=True,
        blank=True,
    )
    nombre_salaries_temps_partiel_par_qualification = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Qualification des salariés travaillant à temps partiel",
        null=True,
        blank=True,
    )
    horaires_temps_partiel = models.TextField(
        verbose_name="Horaires de travail à temps partiel pratiqués dans l'entreprise",
        null=True,
        blank=True,
    )
    programme_prevention_risques_pro = models.TextField(
        verbose_name="Programme annuel de prévention des risques professionnels et d'amélioration des conditions de travail",
        help_text="""prévu au 2° de l'article L. 2312-27 établi à partir des analyses mentionnées à l'article L. 2312-9 et fixant la liste détaillée des mesures devant être prises au cours de l'année à venir dans les mêmes domaines afin de satisfaire, notamment :
            i-Aux principes généraux de prévention prévus aux articles L. 4121-1 à L. 4121-5 et L. 4221-1 ;
            ii-A l'information et à la formation des travailleurs prévues aux articles L. 4141-1 à L. 4143-1 ;
            iii-A l'information et à la formation des salariés titulaires d'un contrat de travail à durée déterminée et des salariés temporaires prévues aux articles L. 4154-2 et L. 4154-4 ;
            iv-A la coordination de la prévention prévue aux articles L. 4522-1 et L. 4522-2 ;
        """,
        null=True,
        blank=True,
    )

    # 1° B - Investissement matériel et immatériel
    # 1° B - a) Evolution des actifs nets d'amortissement et de dépréciations éventuelles (immobilisations)
    evolution_amortissement = models.TextField(
        verbose_name="Evolution des actifs nets d’amortissement et de dépréciations éventuelles (immobilisations)",
        null=True,
        blank=True,
    )
    # 1° B - b) Le cas échéant, dépenses de recherche et développement
    montant_depenses_recherche_developpement = models.IntegerField(
        verbose_name="Dépenses de recherche et développement",
        null=True,
        blank=True,
    )
    # 1° B - c) Mesures envisagées en ce qui concerne l'amélioration, le renouvellement ou la transformation des méthodes de production et d'exploitation ; et incidences de ces mesures sur les conditions de travail et l'emploi ;
    mesures_methodes_production_exploitation = models.TextField(
        verbose_name="Mesures envisagées en ce qui concerne l'amélioration, le renouvellement ou la transformation des méthodes de production et d'exploitation",
        help_text="et incidences de ces mesures sur les conditions de travail et l'emploi",
        null=True,
        blank=True,
    )

    # 2° Egalité professionnelle entre les femmes et les hommes au sein de l'entreprise
    # 2° A - Analyse des données chiffrées
    analyse_egalite_embauche = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière d'embauche",
        null=True,
        blank=True,
    )
    analyse_egalite_formation = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de formation",
        null=True,
        blank=True,
    )
    analyse_egalite_promotion_professionnelle = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de promotion professionnelle",
        null=True,
        blank=True,
    )
    analyse_egalite_qualification = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de qualification",
        null=True,
        blank=True,
    )
    analyse_egalite_classification = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de classification",
        null=True,
        blank=True,
    )
    analyse_egalite_conditions_de_travail = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de conditions de travail",
        null=True,
        blank=True,
    )
    analyse_egalite_sante_et_sécurite = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de santé et de sécurité au travail",
        null=True,
        blank=True,
    )
    analyse_egalite_remuneration = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière de rémunération effective",
        null=True,
        blank=True,
    )
    analyse_egalite_articulation_activite_pro_perso = models.TextField(
        verbose_name="Analyse chiffrée de la situation en matière d'articulation entre l'activité professionnelle et l'exercice de la responsabilité familiale",
        null=True,
        blank=True,
    )
    analyse_ecarts_salaires = models.TextField(
        verbose_name="Analyse des écarts de salaires et de déroulement de carrière",
        help_text="En fonction de leur âge, de leur qualification et de leur ancienneté",
        null=True,
        blank=True,
    )
    evolution_taux_promotion = models.TextField(
        verbose_name="Description de l'évolution des taux de promotion respectifs des femmes et des hommes par métiers dans l'entreprise",
        null=True,
        blank=True,
    )

    # 2° B - Stratégie d'action
    mesures_prises_egalite = models.TextField(
        verbose_name="Mesures prises au cours de l'année écoulée en vue d'assurer l'égalité professionnelle",
        help_text="Bilan des actions de l'année écoulée et, le cas échéant, de l'année précédente. Evaluation du niveau de réalisation des objectifs sur la base des indicateurs retenus. Explications sur les actions prévues non réalisées",
        null=True,
        blank=True,
    )
    objectifs_progression = models.TextField(
        verbose_name="Objectifs de progression pour l'année à venir et indicateurs associés",
        help_text="Définition qualitative et quantitative des mesures permettant de les atteindre conformément à l'article R. 2242-2. Evaluation de leur coût. Echéancier des mesures prévues",
        null=True,
        blank=True,
    )

    # 3° Fonds propres, endettement et impôts
    capitaux_propres = models.IntegerField(
        verbose_name="Capitaux propres de l'entreprise",
        null=True,
        blank=True,
    )
    emprunts_et_dettes_financieres = models.IntegerField(
        verbose_name="Emprunts et dettes financières dont échéances et charges financières",
        null=True,
        blank=True,
    )
    impots_et_taxes = models.IntegerField(
        verbose_name="Impôts et taxes",
        null=True,
        blank=True,
    )

    # 4° Rémunération des salariés et dirigeants, dans l'ensemble de leurs éléments
    # 4° A - Evolution des rémunérations salariales
    # 4° A - a) Frais de personnel y compris cotisations sociales, évolutions salariales par catégorie et par sexe, salaire de base minimum, salaire moyen ou médian, par sexe et par catégorie professionnelle
    frais_personnel = models.IntegerField(
        verbose_name="Frais de personnel, y compris cotisations sociales",
        null=True,
        blank=True,
    )
    evolution_salariale_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        null=True,
        blank=True,
    )
    evolution_salariale_par_sexe = CategoryField(
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )
    salaire_base_minimum_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Salaire de base minimum par catégorie",
        null=True,
        blank=True,
    )
    salaire_base_minimum_par_sexe = CategoryField(
        verbose_name="Salaire de base minimum par sexe",
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )
    salaire_moyen_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Salaire moyen par catégorie",
        null=True,
        blank=True,
    )
    salaire_moyen_par_sexe = CategoryField(
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )
    salaire_median_par_categorie = CategoryField(
        category_type=CategoryType.PROFESSIONNELLE,
        verbose_name="Salaire médian par catégorie",
        null=True,
        blank=True,
    )
    salaire_median_par_sexe = CategoryField(
        verbose_name="Salaire médian par sexe",
        categories=["homme", "femme"],
        null=True,
        blank=True,
    )
    # 4° A - b) Pour les entreprises soumises aux dispositions de l'article L. 225-115 du code de commerce, montant global des rémunérations visées au 4° de cet article
    # https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038610196/
    montant_global_hautes_remunerations = models.IntegerField(
        verbose_name="Montant global des hautes rémunérations",
        help_text="Montant global, certifié exact par les commissaires aux comptes, s'il en existe, des rémunérations versées aux personnes les mieux rémunérées, le nombre de ces personnes étant de dix ou de cinq selon que l'effectif du personnel excède ou non deux cents salariés ; uniquement pour les entreprises soumises aux dispositions de l'article L. 225-115 du code de commerce",
        null=True,
        blank=True,
    )
    # 4° A - c) Epargne salariale : intéressement, participation
    epargne_salariale = models.TextField(
        verbose_name="Epargne salariale : intéressement, participation",
        null=True,
        blank=True,
    )

    # 5° Activités sociales et culturelles
    montant_contribution_activites_sociales_culturelles = models.IntegerField(
        verbose_name="Montant de la contribution aux activités sociales et culturelles",
        help_text="Du comité social et économique",
        null=True,
        blank=True,
    )
    mecenat_verse = models.IntegerField(
        verbose_name="Mécénat versé",
        null=True,
        blank=True,
    )

    # 6° Rémunération des financeurs, en dehors des éléments mentionnés au 4°
    # 6° A - Rémunération des actionnaires (revenus distribués)
    remuneration_actionnaires = models.IntegerField(
        verbose_name="Rémunération des actionnaires (revenus distribués)",
        null=True,
        blank=True,
    )

    # 6° B - Rémunération de l'actionnariat salarié
    remuneration_actionnariat_salarie = models.IntegerField(
        verbose_name="Rémunération de l'actionnariat salarié (montant des actions détenues dans le cadre de l'épargne salariale, part dans le capital, dividendes reçus)",
        null=True,
        blank=True,
    )

    # 7° Flux financiers à destination de l'entreprise
    # 7° A - Aides publiques
    aides_financieres = models.TextField(
        verbose_name="Les aides ou avantages financiers consentis à l'entreprise par l'Union européenne, l'Etat, une collectivité territoriale, un de leurs établissements publics ou un organisme privé chargé d'une mission de service public, et leur utilisation",
        help_text="Pour chacune de ces aides, l'employeur indique la nature de l'aide, son objet, son montant, les conditions de versement et d'emploi fixées, le cas échéant, par la personne publique qui l'attribue et son utilisation",
        null=True,
        blank=True,
    )

    # 7° B - Réductions d'impôts
    reductions_impots = models.IntegerField(
        verbose_name="Réductions d'impôts",
        null=True,
        blank=True,
    )

    # 7° C - Exonérations et réductions de cotisations sociales
    exonerations_cotisations_sociales = models.IntegerField(
        verbose_name="Exonérations et réductions de cotisations sociales",
        null=True,
        blank=True,
    )

    # 7° D - Crédits d'impôts
    credits_impots = models.IntegerField(
        verbose_name="Crédits d'impôts",
        null=True,
        blank=True,
    )

    # 7° E - Mécénat
    mecenat_recu = models.IntegerField(
        verbose_name="Mécénat reçu",
        null=True,
        blank=True,
    )

    # 7° F - Résultats financiers
    chiffre_affaires = models.IntegerField(
        verbose_name=" Le chiffre d'affaires",
        null=True,
        blank=True,
    )
    benefices_ou_pertes = models.IntegerField(
        verbose_name="Les bénéfices ou pertes constatés",
        null=True,
        blank=True,
    )
    resultats_globaux = CategoryField(
        categories=["valeur", "volume"],
        verbose_name="Les résultats globaux de la production",
        null=True,
        blank=True,
    )
    affectation_benefices = models.TextField(
        verbose_name="L'affectation des bénéfices réalisés",
        null=True,
        blank=True,
    )  # TODO: à remplacer par un CategoryField et les affectations possibles ?

    # 8° Partenariats
    # 8° A - Partenariats conclus pour produire des services ou des produits pour une autre entreprise
    partenariats_pour_produire = models.TextField(
        verbose_name="Partenariats conclus pour produire des services ou des produits pour une autre entreprise",
        null=True,
        blank=True,
    )

    # 8° B - Partenariats conclus pour bénéficier des services ou des produits d'une autre entreprise
    partenariats_pour_beneficier = models.TextField(
        verbose_name="Partenariats conclus pour bénéficier des services ou des produits d'une autre entreprise",
        null=True,
        blank=True,
    )
    # 9° Pour les entreprises appartenant à un groupe, transferts commerciaux et financiers entre les entités du groupe
    # 9° A - Transferts de capitaux tels qu'ils figurent dans les comptes individuels des sociétés du groupe lorsqu'ils présentent une importance significative
    transferts_de_capitaux = models.TextField(
        verbose_name="Transferts de capitaux tels qu'ils figurent dans les comptes individuels des sociétés du groupe lorsqu'ils présentent une importance significative",
        null=True,
        blank=True,
    )

    # 9° B - Cessions, fusions, et acquisitions réalisées
    cessions_fusions_acquisitions = models.TextField(
        verbose_name="Cessions, fusions, et acquisitions réalisées",
        null=True,
        blank=True,
    )

    # 10° Environnement
    # 10° A - Politique générale en matière environnementale
    prise_en_compte_questions_environnementales = models.TextField(
        verbose_name="Organisation de l'entreprise pour prendre en compte les questions environnementales",
        help_text="et, le cas échéant, les démarches d'évaluation ou de certification en matière d'environnement",
        null=True,
        blank=True,
    )

    # 10° B - Economie circulaire
    # 10° B - a) Prévention et gestion de la production de déchets
    quantite_de_dechets_dangereux = models.TextField(
        verbose_name="évaluation de la quantité de déchets dangereux définis à l'article R. 541-8 du code de l'environnement et faisant l'objet d'une émission du bordereau mentionné à l'article R. 541-45 du même code",
        null=True,
        blank=True,
    )
    # 10° B - b) Utilisation durable des ressources
    consommation_eau = models.IntegerField(
        verbose_name="consommation d'eau",
        null=True,
        blank=True,
    )
    consommation_energie = models.IntegerField(
        verbose_name="consommation d'énergie",
        null=True,
        blank=True,
    )

    # 10° C - Changement climatique
    # 10° C - a) Identification des postes d'émissions directes de gaz à effet de serre produites par les sources fixes et mobiles nécessaires aux activités de l'entreprise (communément appelées " émissions du scope 1 ") et, lorsque l'entreprise dispose de cette information, évaluation du volume de ces émissions de gaz à effet de serre ;
    postes_emissions_directes_gaz_effet_de_serre = models.TextField(
        verbose_name="Identification des postes d'émissions directes de gaz à effet de serre",
        help_text="produites par les sources fixes et mobiles nécessaires aux activités de l'entreprise (communément appelées \"émissions du scope 1\") et, lorsque l'entreprise dispose de cette information, évaluation du volume de ces émissions de gaz à effet de serre ",
        null=True,
        blank=True,
    )
    # 10° C - b) Bilan des émissions de gaz à effet de serre prévu par l'article L. 229-25 du code de l'environnement ou bilan simplifié prévu par l'article 244 de la loi n° 2020-1721 du 29 décembre 2020 de finances pour 2021 pour les entreprises tenues d'établir ces différents bilans.
    bilan_gaz_effet_de_serre = models.TextField(
        verbose_name="Bilan des émissions de gaz à effet de serre prévu par l'article L. 229-25 du code de l'environnement ou bilan simplifié prévu par l'article 244 de la loi n° 2020-1721 du 29 décembre 2020 de finances pour 2021 pour les entreprises tenues d'établir ces différents bilans",
        null=True,
        blank=True,
    )


class PersonalBDESEAvecAccord(BDESEAvecAccord):
    class Meta:
        proxy = True
        verbose_name = "BDESE personnelle avec accord d'entreprise"
        verbose_name_plural = "BDESE personnelles avec accord d'entreprise"

    objects = PersonalManager()


class OfficialBDESEAvecAccord(BDESEAvecAccord):
    class Meta:
        proxy = True
        verbose_name = "BDESE officielle avec accord d'entreprise"
        verbose_name_plural = "BDESE officielles avec accord d'entreprise"

    objects = OfficialManager()


class PersonalBDESE_300(BDESE_300):
    class Meta:
        proxy = True
        verbose_name = "BDESE personnelle plus de 300 salariés"
        verbose_name_plural = "BDESE personnelles plus de 300 salariés"

    objects = PersonalManager()


class OfficialBDESE_300(BDESE_300):
    class Meta:
        proxy = True
        verbose_name = "BDESE officielle plus de 300 salariés"
        verbose_name_plural = "BDESE officielles plus de 300 salariés"

    objects = OfficialManager()


class PersonalBDESE_50_300(BDESE_50_300):
    class Meta:
        proxy = True
        verbose_name = "BDESE personnelle 50 à 300 salariés"
        verbose_name_plural = "BDESE personnelles 50 à 300 salariés"

    objects = PersonalManager()


class OfficialBDESE_50_300(BDESE_50_300):
    class Meta:
        proxy = True
        verbose_name = "BDESE officielle 50 à 300 salariés"
        verbose_name_plural = "BDESE officielles 50 à 300 salariés"

    objects = OfficialManager()


def get_all_official_bdese(entreprise):
    bdese_50_300 = BDESE_50_300.officials.filter(entreprise=entreprise)
    bdese_300 = BDESE_300.officials.filter(entreprise=entreprise)
    bdese_avec_accord = BDESEAvecAccord.officials.filter(entreprise=entreprise)
    return chain(bdese_50_300, bdese_300, bdese_avec_accord)


def get_all_personal_bdese(entreprise, user):
    bdese_50_300 = BDESE_50_300.personals.filter(entreprise=entreprise, user=user)
    bdese_300 = BDESE_300.personals.filter(entreprise=entreprise, user=user)
    bdese_avec_accord = BDESEAvecAccord.personals.filter(
        entreprise=entreprise, user=user
    )
    return chain(bdese_50_300, bdese_300, bdese_avec_accord)


def has_official_bdese(entreprise: Entreprise) -> bool:
    try:
        next(get_all_official_bdese(entreprise))
        return True
    except StopIteration:
        return False
