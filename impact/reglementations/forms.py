import json

from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import DENOMINATION_MAX_LENGTH
from reglementations.models import CategoryType
from utils.forms import DsfrForm


class SimulationForm(DsfrForm, forms.ModelForm):
    denomination = forms.CharField()
    siren = forms.CharField()
    appartient_groupe = forms.BooleanField(
        required=False,
        label="L'entreprise appartient à un groupe composé d'une société-mère et d'une ou plusieurs filiales",
    )
    comptes_consolides = forms.BooleanField(
        required=False,
        label="Le groupe d'entreprises établit des comptes consolidés",
    )

    class Meta:
        model = CaracteristiquesAnnuelles
        fields = [
            "effectif",
            "tranche_chiffre_affaires",
            "tranche_bilan",
            "tranche_chiffre_affaires_consolide",
            "tranche_bilan_consolide",
        ]
        help_texts = {
            "tranche_chiffre_affaires": "Sélectionnez le chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Sélectionnez le bilan de l'exercice clos",
        }

    def clean_denomination(self):
        denomination = self.cleaned_data.get("denomination")
        return denomination[:DENOMINATION_MAX_LENGTH]

    def clean(self):
        cleaned_data = super().clean()
        appartient_groupe = cleaned_data.get("appartient_groupe")
        if not appartient_groupe:
            cleaned_data["comptes_consolides"] = False
        comptes_consolides = cleaned_data.get("comptes_consolides")
        tranche_chiffre_affaires_consolide = cleaned_data.get(
            "tranche_chiffre_affaires_consolide"
        )
        tranche_bilan_consolide = cleaned_data.get("tranche_bilan_consolide")
        if comptes_consolides:
            ERREUR = "Ce champ est obligatoire lorsque les comptes sont consolidés"
            if not tranche_chiffre_affaires_consolide:
                self.add_error("tranche_chiffre_affaires_consolide", ERREUR)
            if not tranche_bilan_consolide:
                self.add_error("tranche_bilan_consolide", ERREUR)
        else:
            if tranche_chiffre_affaires_consolide:
                cleaned_data["tranche_chiffre_affaires_consolide"] = None
            if tranche_bilan_consolide:
                cleaned_data["tranche_bilan_consolide"] = None


class IntroductionDemoForm(DsfrForm):
    external_fields_in_step = forms.JSONField(required=False, initial=[])
    example_field = forms.CharField(
        label="Exemple de champ",
        help_text="Exemple d'information obligatoire à renseigner dans la BDESE",
        required=False,
    )


class ListJSONWidget(forms.widgets.MultiWidget):
    template_name = "snippets/list_json_widget.html"

    def __init__(self, subwidgets_label, subwidgets_number):
        subwidgets = [
            forms.widgets.TextInput(
                attrs={"class": "fr-input", "label": subwidgets_label}
            )
            for i in range(subwidgets_number)
        ]
        super().__init__(subwidgets)

    def decompress(self, value):
        if isinstance(value, list):
            return value
        elif isinstance(value, str) and value != "null":
            values = json.loads(value)
            value = [value for value in values if value is not None]
            return value
        return []

    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name)
        not_empty_values = [value for value in values if value]
        # JSONField expects a single string that it can parse into json.
        return json.dumps(not_empty_values)


class BDESEConfigurationForm(forms.ModelForm, DsfrForm):
    class Meta:
        fields = ["categories_professionnelles"]
        help_texts = {
            "categories_professionnelles": "Une structure de qualification comprenant <strong>trois postes minimum</strong> est requise pour certains indicateurs. Il est souhaitable de faire référence à la classification de la convention collective, de l'accord d'entreprise et aux pratiques habituellement retenues dans l'entreprise.<br> A titre d'exemple la répartition suivante peut être retenue : cadres ; employés ; techniciens et agents de maîtrise (ETAM) ; et ouvriers.",
            "categories_professionnelles_detaillees": "Une structure de qualification détaillée comprenant <strong>cinq postes minimum</strong> est requise pour d'autres indicateurs. Il est à nouveau souhaitable de faire référence à la classification de la convention collective, de l'accord d'entreprise et aux pratiques habituellement retenues dans l'entreprise.<br> A titre d'exemple, la répartition suivante des postes peut être retenue : cadres ; techniciens ; agents de maîtrise ; employés qualifiés ; employés non qualifiés ; ouvriers qualifiés ; ouvriers non qualifiés.",
            "niveaux_hierarchiques": "Une classification selon le niveau ou coefficient hiérarchique pertinente au sein de l'entreprise comprenant <strong>deux niveaux minimum</strong>. Libre à l'employeur d'apprécier quelle est la catégorie la plus pertinente : classification conventionnelle ou niveau managérial.",
        }
        widgets = {
            "categories_professionnelles": ListJSONWidget("Poste", 6),
            "categories_professionnelles_detaillees": ListJSONWidget("Poste", 8),
            "niveaux_hierarchiques": ListJSONWidget("Niveau", 6),
        }

    def clean_categories_professionnelles(self):
        data = self.cleaned_data["categories_professionnelles"]
        if len(data) < 3:
            raise ValidationError("Au moins 3 postes sont requis")
        return data

    def clean_categories_professionnelles_detaillees(self):
        data = self.cleaned_data["categories_professionnelles_detaillees"]
        if len(data) < 5:
            raise ValidationError("Au moins 5 postes sont requis")
        return data

    def clean_niveaux_hierarchiques(self):
        data = self.cleaned_data["niveaux_hierarchiques"]
        if len(data) < 2:
            raise ValidationError("Au moins 2 niveaux sont requis")
        return data


def bdese_configuration_form_factory(bdese, *args, **kwargs):
    fields = ["categories_professionnelles"]
    if bdese.is_bdese_300:
        fields.extend(
            ["categories_professionnelles_detaillees", "niveaux_hierarchiques"]
        )

    Form = forms.modelform_factory(
        bdese.__class__,
        form=BDESEConfigurationForm,
        fields=fields,
    )

    form = Form(*args, instance=bdese, **kwargs)

    if bdese.step_is_complete(0):
        for field in form.fields:
            form.fields[field].disabled = True

    return form


class CategoryJSONWidget(forms.MultiWidget):
    template_name = "snippets/category_json_widget.html"

    def __init__(self, categories, widgets=None, attrs=None):
        self.categories = categories
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if type(value) != dict:
            return []
        return [value.get(category) for category in self.categories]

    def id_for_label(self, id_):
        return id_


def bdese_form_factory(
    bdese,
    step,
    fetched_data=None,
    *args,
    **kwargs,
):
    class CategoryMultiValueField(forms.MultiValueField):
        widget = CategoryJSONWidget

        def __init__(
            self,
            base_field=forms.IntegerField,
            category_type=CategoryType.HARD_CODED,
            categories=None,
            encoder=None,
            decoder=None,
            *args,
            **kwargs,
        ):
            """https://docs.djangoproject.com/en/4.1/ref/forms/fields/#django.forms.MultiValueField.require_all_fields"""
            self.base_field = base_field
            if category_type == CategoryType.PROFESSIONNELLE:
                categories = bdese.categories_professionnelles
            elif category_type == CategoryType.PROFESSIONNELLE_DETAILLEE:
                categories = bdese.categories_professionnelles_detaillees
            elif category_type == CategoryType.HIERARCHIQUE:
                categories = bdese.niveaux_hierarchiques
            self.categories = categories or []

            fields = [base_field() for category in self.categories]
            widgets = [
                base_field.widget({"label": category})
                for category in self.categories
                if hasattr(base_field, "widget")
            ]
            super().__init__(
                fields=fields,
                widget=CategoryJSONWidget(
                    self.categories, widgets, attrs={"class": "fr-input"}
                ),
                require_all_fields=False,
                *args,
                **kwargs,
            )

        def compress(self, data_list):
            if data_list:
                return dict(zip(self.categories, data_list))
            return None

    class BDESEForm(forms.ModelForm, DsfrForm):
        external_fields_in_step = forms.JSONField(required=False)

        class Meta:
            model = bdese.__class__
            fields = []
            field_classes = {
                category_field: CategoryMultiValueField
                for category_field in bdese.__class__.category_fields()
            }
            widgets = {
                boolean_field.name: forms.CheckboxInput
                for boolean_field in bdese._meta.get_fields()
                if type(boolean_field) == models.BooleanField
            }

        def __init__(self, bdese, fetched_data=None, *args, **kwargs):
            if fetched_data:
                if "initial" not in kwargs:
                    kwargs["initial"] = {}
                kwargs["initial"].update(fetched_data)
            super().__init__(*args, instance=bdese, **kwargs)
            if step == "all" or bdese.step_is_complete(step):
                for field in self.fields:
                    self.fields[field].disabled = True
            elif fetched_data:
                for field in fetched_data:
                    if field in self.fields:
                        self.fields[field].fetched_data = fetched_data[field]
            self.fields["external_fields_in_step"].initial = [
                field_name
                for field_name in bdese.external_fields
                if field_name in self.fields
            ]

        def save(self, commit=True):
            bdese = super().save(commit=False)
            if "external_fields_in_step" in self.changed_data:
                old_external_fields = bdese.external_fields
                new_external_fields = self.update_external_fields(
                    self.cleaned_data["external_fields_in_step"] or [],
                    old_external_fields,
                )
                bdese.external_fields = new_external_fields
            if commit:
                bdese.save()
            return bdese

        def update_external_fields(
            self, external_fields_in_step: list, old_external_fields: list
        ) -> list:
            new_external_fields = old_external_fields
            for field_name in self.fields:
                if (
                    field_name in external_fields_in_step
                    and field_name not in old_external_fields
                ):
                    new_external_fields.append(field_name)
                elif (
                    field_name in old_external_fields
                    and field_name not in external_fields_in_step
                ):
                    new_external_fields.remove(field_name)
            return new_external_fields

    bdese_model_class = bdese.__class__
    Form = forms.modelform_factory(
        bdese_model_class,
        form=BDESEForm,
        fields=BDESE_300_FIELDS[step]
        if bdese.is_bdese_300
        else BDESE_50_300_FIELDS[step],
    )
    return Form(bdese, fetched_data=fetched_data, *args, **kwargs)


BDESE_50_300_FIELDS = {
    1: [
        "effectif_mensuel",
        "effectif_cdi",
        "effectif_cdd",
        "nombre_salaries_temporaires",
        "nombre_travailleurs_exterieurs",
        "nombre_journees_salaries_temporaires",
        "nombre_contrats_insertion_formation_jeunes",
        "motifs_contrats_cdd_temporaire_temps_partiel_exterieurs",
        "effectif_homme",
        "effectif_femme",
        "actions_prevention_formation",
        "actions_emploi_personnes_handicapees",
        "doeth",
        "evolution_nombre_stagiaires",
        "orientations_formation_professionnelle",
        "resultat_negociations_L_2241_6",
        "conclusions_verifications_L_6361_1_L_6323_13_L_6362_4",
        "bilan_actions_plan_formation",
        "informations_conges_formation",
        "nombre_salaries_beneficaires_abondement",
        "somme_abondement",
        "nombre_salaries_beneficiaires_entretien_professionnel",
        "bilan_contrats_alternance",
        "emplois_periode_professionnalisation",
        "effectif_periode_professionnalisation_par_age",
        "effectif_periode_professionnalisation_par_sexe",
        "effectif_periode_professionnalisation_par_niveau_initial",
        "resultats_periode_professionnalisation",
        "bilan_cpf",
        "nombre_salaries_temps_partiel_par_sexe",
        "nombre_salaries_temps_partiel_par_qualification",
        "horaires_temps_partiel",
        "programme_prevention_risques_pro",
    ],
    2: [
        "evolution_amortissement",
        "montant_depenses_recherche_developpement",
        "mesures_methodes_production_exploitation",
    ],
    3: [
        "analyse_egalite_embauche",
        "analyse_egalite_formation",
        "analyse_egalite_promotion_professionnelle",
        "analyse_egalite_qualification",
        "analyse_egalite_classification",
        "analyse_egalite_conditions_de_travail",
        "analyse_egalite_sante_et_sécurite",
        "analyse_egalite_remuneration",
        "analyse_egalite_articulation_activite_pro_perso",
        "analyse_ecarts_salaires",
        "evolution_taux_promotion",
        "mesures_prises_egalite",
        "objectifs_progression",
    ],
    4: [
        "capitaux_propres",
        "emprunts_et_dettes_financieres",
        "impots_et_taxes",
    ],
    5: [
        "frais_personnel",
        "evolution_salariale_par_categorie",
        "evolution_salariale_par_sexe",
        "salaire_base_minimum_par_categorie",
        "salaire_base_minimum_par_sexe",
        "salaire_moyen_par_categorie",
        "salaire_moyen_par_sexe",
        "salaire_median_par_categorie",
        "salaire_median_par_sexe",
        "montant_global_hautes_remunerations",
        "epargne_salariale",
    ],
    6: [
        "montant_contribution_activites_sociales_culturelles",
        "mecenat_verse",
    ],
    7: [
        "remuneration_actionnaires",
        "remuneration_actionnariat_salarie",
    ],
    8: [
        "aides_financieres",
        "reductions_impots",
        "exonerations_cotisations_sociales",
        "credits_impots",
        "mecenat_recu",
        "chiffre_affaires",
        "benefices_ou_pertes",
        "resultats_globaux",
        "affectation_benefices",
    ],
    9: [
        "partenariats_pour_produire",
        "partenariats_pour_beneficier",
    ],
    10: [
        "transferts_de_capitaux",
        "cessions_fusions_acquisitions",
    ],
    11: [
        "prise_en_compte_questions_environnementales",
        "quantite_de_dechets_dangereux",
        "consommation_eau",
        "consommation_energie",
        "postes_emissions_directes_gaz_effet_de_serre",
        "bilan_gaz_effet_de_serre",
    ],
}

BDESE_300_FIELDS = {
    1: [
        "effectif_total",
        "effectif_permanent",
        "effectif_cdd",
        "effectif_mensuel_moyen",
        "effectif_homme",
        "effectif_femme",
        "effectif_age",
        "effectif_anciennete",
        "effectif_nationalite_francaise",
        "effectif_nationalite_etrangere",
        "effectif_qualification_detaillee_homme",
        "effectif_qualification_detaillee_femme",
        "nombre_travailleurs_exterieurs",
        "nombre_stagiaires",
        "nombre_moyen_mensuel_salaries_temporaires",
        "duree_moyenne_contrat_de_travail_temporaire",
        "nombre_salaries_de_l_entreprise_detaches",
        "nombre_salaries_detaches_accueillis",
        "nombre_embauches_cdi",
        "nombre_embauches_cdd",
        "nombre_embauches_jeunes",
        "total_departs",
        "nombre_demissions",
        "nombre_licenciements_economiques",
        "nombre_licenciements_autres",
        "nombre_fin_cdd",
        "nombre_fin_periode_essai",
        "nombre_mutations",
        "nombre_departs_volontaires_retraite_preretraite",
        "nombre_deces",
        "nombre_promotions",
        "nombre_salaries_chomage_partiel",
        "nombre_heures_chomage_partiel_indemnisees",
        "nombre_heures_chomage_partiel_non_indemnisees",
        "nombre_salaries_chomage_intemperies",
        "nombre_heures_chomage_intemperies_indemnisees",
        "nombre_heures_chomage_intemperies_non_indemnisees",
        "nombre_travailleurs_handicapés",
        "nombre_travailleurs_handicapes_accidents_du_travail",
        "evolution_nombre_stagiaires",
        "pourcentage_masse_salariale_formation_continue",
        "montant_formation_continue",
        "nombre_stagiaires_formation_continue_homme",
        "nombre_stagiaires_formation_continue_femme",
        "nombre_heures_stage_remunerees_homme",
        "nombre_heures_stage_remunerees_femme",
        "nombre_heures_stage_non_remunerees_homme",
        "nombre_heures_stage_non_remunerees_femme",
        "type_stages",
        "nombre_salaries_conge_formation_remunere",
        "nombre_salaries_conge_formation_non_remunere",
        "nombre_salaries_conge_formation_refuse",
        "nombre_contrats_apprentissage",
        "nombre_incapacites_permanentes_partielles",
        "nombre_incapacites_permanentes_totales",
        "nombre_accidents_travail_mortels",
        "nombre_accidents_trajet_mortels",
        "nombre_accidents_trajet_avec_arret_travail",
        "nombre_accidents_salaries_temporaires_ou_prestataires",
        "taux_cotisation_securite_sociale_accidents_travail",
        "montant_cotisation_securite_sociale_accidents_travail",
        "nombre_accidents_existence_risques_graves",
        "nombre_accidents_chutes_dénivellation",
        "nombre_accidents_machines",
        "nombre_accidents_circulation_manutention_stockage",
        "nombre_accidents_objets_en_mouvement",
        "nombre_accidents_autres",
        "nombre_maladies_professionnelles",
        "denomination_maladies_professionnelles",
        "nombre_salaries_affections_pathologiques",
        "caracterisation_affections_pathologiques",
        "nombre_declaration_procedes_travail_dangereux",
        "effectif_forme_securite",
        "montant_depenses_formation_securite",
        "taux_realisation_programme_securite",
        "nombre_plans_specifiques_securite",
        "horaire_hebdomadaire_moyen",
        "nombre_salaries_repos_compensateur_code_travail",
        "nombre_salaries_repos_compensateur_regime_conventionne",
        "nombre_salaries_horaires_individualises",
        "nombre_salaries_temps_partiel_20_30_heures",
        "nombre_salaries_temps_partiel_autres",
        "nombre_salaries_2_jours_repos_hebdomadaire_consecutifs",
        "nombre_moyen_jours_conges_annuels",
        "nombre_jours_feries_payes",
        "unite_absenteisme",
        "nombre_unites_absence",
        "nombre_unites_theoriques_travaillees",
        "nombre_unites_absence_maladie",
        "nombre_unites_absence_maladie_par_duree",
        "nombre_unites_absence_accidents",
        "nombre_unites_absence_maternite",
        "nombre_unites_absence_conges_autorises",
        "nombre_unites_absence_autres",
        "nombre_personnes_horaires_alternant_ou_nuit",
        "nombre_personnes_horaires_alternant_ou_nuit_50_ans",
        "nombre_taches_repetitives",
        "nombre_personnes_exposees_bruit",
        "nombre_salaries_exposes_temperatures",
        "nombre_salaries_exposes_temperatures_extremes",
        "nombre_salaries_exposes_intemperies",
        "nombre_analyses_produits_toxiques",
        "experiences_transformation_organisation_travail",
        "montant_depenses_amelioration_conditions_travail",
        "taux_realisation_programme_amelioration_conditions_travail",
        "nombre_visites_medicales",
        "nombre_examens_medicaux",
        "nombre_examens_medicaux_complementaires",
        "pourcentage_temps_medecin_du_travail",
        "nombre_salaries_inaptes",
        "nombre_salaries_reclasses",
    ],
    2: [
        "evolution_amortissement",
        "montant_depenses_recherche_developpement",
        "evolution_productivite",
    ],
    3: [
        "nombre_CDI_homme",
        "nombre_CDI_femme",
        "nombre_CDD_homme",
        "nombre_CDD_femme",
        "effectif_par_duree_homme",
        "effectif_par_duree_femme",
        "effectif_par_organisation_du_travail_homme",
        "effectif_par_organisation_du_travail_femme",
        "conges_homme",
        "conges_femme",
        "conges_par_type_homme",
        "conges_par_type_femme",
        "embauches_CDI_homme",
        "embauches_CDI_femme",
        "embauches_CDD_homme",
        "embauches_CDD_femme",
        "departs_retraite_homme",
        "departs_demission_homme",
        "departs_fin_CDD_homme",
        "departs_licenciement_homme",
        "departs_retraite_femme",
        "departs_demission_femme",
        "departs_fin_CDD_femme",
        "departs_licenciement_femme",
        "effectif_par_niveau_hierarchique_homme",
        "effectif_par_niveau_hierarchique_femme",
        "nombre_promotions_homme",
        "nombre_promotions_femme",
        "duree_moyenne_entre_deux_promotions_homme",
        "duree_moyenne_entre_deux_promotions_femme",
        "anciennete_moyenne_homme",
        "anciennete_moyenne_femme",
        "anciennete_moyenne_dans_categorie_profesionnelle_homme",
        "anciennete_moyenne_dans_categorie_profesionnelle_femme",
        "anciennete_moyenne_par_niveau_hierarchique_homme",
        "anciennete_moyenne_par_niveau_hierarchique_femme",
        "anciennete_moyenne_dans_niveau_hierarchique_homme",
        "anciennete_moyenne_dans_niveau_hierarchique_femme",
        "age_moyen_homme",
        "age_moyen_femme",
        "age_moyen_par_niveau_hierarchique_homme",
        "age_moyen_par_niveau_hierarchique_femme",
        "remuneration_moyenne_ou_mediane",
        "remuneration_homme",
        "remuneration_femme",
        "remuneration_par_niveau_hierarchique_homme",
        "remuneration_par_niveau_hierarchique_femme",
        "remuneration_par_age_homme",
        "remuneration_par_age_femme",
        "nombre_femmes_plus_hautes_remunerations",
        "nombre_moyen_heures_formation_homme",
        "nombre_moyen_heures_formation_femme",
        "action_adaptation_au_poste_homme",
        "action_adaptation_au_poste_femme",
        "action_maintien_emploi_homme",
        "action_maintien_emploi_femme",
        "action_developpement_competences_homme",
        "action_developpement_competences_femme",
        "exposition_risques_pro_homme",
        "exposition_risques_pro_femme",
        "accidents_homme",
        "accidents_femme",
        "nombre_accidents_travail_avec_arret_homme",
        "nombre_accidents_travail_avec_arret_femme",
        "nombre_accidents_trajet_avec_arret_homme",
        "nombre_accidents_trajet_avec_arret_femme",
        "nombre_accidents_par_elements_materiels_homme",
        "nombre_accidents_par_elements_materiels_femme",
        "nombre_et_denominations_maladies_pro_homme",
        "nombre_et_denominations_maladies_pro_femme",
        "nombre_journees_absence_accident_homme",
        "nombre_journees_absence_accident_femme",
        "maladies_homme",
        "maladies_femme",
        "maladies_avec_examen_de_reprise_homme",
        "maladies_avec_examen_de_reprise_femme",
        "complement_salaire_conge_paternite",
        "complement_salaire_conge_maternite",
        "complement_salaire_conge_adoption",
        "nombre_jours_conges_paternite_pris",
        "existence_orga_facilitant_vie_familiale_et_professionnelle",
        "nombre_salaries_temps_partiel_choisi_homme",
        "nombre_salaries_temps_partiel_choisi_femme",
        "nombre_salaries_temps_partiel_choisi_vers_temps_plein_homme",
        "nombre_salaries_temps_partiel_choisi_vers_temps_plein_femme",
        "participation_accueil_petite_enfance",
        "evolution_depenses_credit_impot_famille",
        "mesures_prises_egalite",
        "objectifs_progression",
    ],
    4: [
        "capitaux_propres",
        "emprunts_et_dettes_financieres",
        "impots_et_taxes",
    ],
    5: [
        "frais_personnel",
        "evolution_salariale_par_categorie",
        "evolution_salariale_par_sexe",
        "salaire_base_minimum_par_categorie",
        "salaire_base_minimum_par_sexe",
        "salaire_moyen_par_categorie",
        "salaire_moyen_par_sexe",
        "salaire_median_par_categorie",
        "salaire_median_par_sexe",
        "rapport_masse_salariale_effectif_mensuel_homme",
        "rapport_masse_salariale_effectif_mensuel_femme",
        "remuneration_moyenne_decembre_homme",
        "remuneration_moyenne_decembre_femme",
        "remuneration_mensuelle_moyenne_homme",
        "remuneration_mensuelle_moyenne_femme",
        "part_primes_non_mensuelle_homme",
        "part_primes_non_mensuelle_femme",
        "remunerations",
        "rapport_moyenne_deciles",
        "rapport_moyenne_cadres_ouvriers",
        "montant_10_remunerations_les_plus_eleves",
        "pourcentage_salaries_primes_de_rendement",
        "pourcentage_ouvriers_employes_payes_au_mois",
        "charge_salariale_globale",
        "montant_global_hautes_remunerations",
        "montant_global_reserve_de_participation",
        "montant_moyen_participation",
        "part_capital_detenu_par_salaries",
        "avantages_sociaux",
        "remuneration_dirigeants_mandataires_sociaux",
    ],
    6: [
        "composition_CSE_etablissement",
        "participation_elections",
        "volume_credit_heures",
        "nombre_reunion_representants_personnel",
        "accords_conclus",
        "nombre_personnes_conge_education_ouvriere",
        "nombre_heures_reunion_personnel",
        "elements_systeme_accueil",
        "elements_systeme_information",
        "elements_systeme_entretiens_individuels",
        "differends_application_droit_du_travail",
        "contributions_financement_CSE_CSEE",
        "contributions_autres_depenses",
        "cout_prestations_maladie_deces",
        "cout_prestations_vieillesse",
        "equipements_pour_conditions_de_vie",
    ],
    7: ["remuneration_actionnaires", "remuneration_actionnariat_salarie"],
    8: [
        "aides_financieres",
        "reductions_impots",
        "exonerations_cotisations_sociales",
        "credits_impots",
        "mecenat",
        "chiffre_affaires",
        "benefices_ou_pertes",
        "resultats_globaux",
        "affectation_benefices",
    ],
    9: ["partenariats_pour_produire", "partenariats_pour_beneficier"],
    10: ["transferts_de_capitaux", "cessions_fusions_acquisitions"],
    11: [
        "informations_environnementales",
        "quantite_de_dechets_dangereux_soumis_DPEF",
        "bilan_gaz_effet_de_serre_soumis_DPEF",
        "prise_en_compte_questions_environnementales",
        "quantite_de_dechets_dangereux_non_soumis_DPEF",
        "consommation_eau",
        "consommation_energie",
        "postes_emissions_directes_gaz_effet_de_serre",
        "bilan_gaz_effet_de_serre_non_soumis_DPEF",
    ],
}
