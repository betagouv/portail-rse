from django import forms

from public.forms import DsfrForm
from .models import BDESE_50_300, BDESE_300


class CategoryJSONWidget(forms.MultiWidget):
    template_name = "snippets/category_json_widget.html"

    def __init__(self, categories, widgets=None, attrs=None):
        self.categories = categories
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if type(value) != dict:
            return []
        return [value.get(category) for category in self.categories]


def bdese_form_factory(
    step, categories_professionnelles, instance, fetched_data=None, *args, **kwargs
):
    class CategoryMultiValueField(forms.MultiValueField):
        widget = CategoryJSONWidget

        def __init__(
            self,
            base_field=forms.IntegerField,
            categories=None,
            encoder=None,
            decoder=None,
            *args,
            **kwargs
        ):
            """https://docs.djangoproject.com/en/4.1/ref/forms/fields/#django.forms.MultiValueField.require_all_fields"""
            self.categories = categories or categories_professionnelles
            fields = [base_field() for category in self.categories]
            widgets = [
                base_field.widget({"label": category}) for category in self.categories
            ]
            super().__init__(
                fields=fields,
                widget=CategoryJSONWidget(
                    self.categories, widgets, attrs={"class": "fr-input"}
                ),
                require_all_fields=False,
                *args,
                **kwargs
            )

        def compress(self, data_list):
            if data_list:
                return dict(zip(self.categories, data_list))
            return None

    class BDESEForm(forms.ModelForm, DsfrForm):
        class Meta:
            model = instance.__class__
            fields = []
            field_classes = {
                category_field: CategoryMultiValueField
                for category_field in instance.__class__.category_fields()
            }

        def __init__(self, fetched_data=None, *args, **kwargs):
            if fetched_data:
                if "initial" not in kwargs:
                    kwargs["initial"] = {}
                kwargs["initial"].update(fetched_data)
            super().__init__(*args, **kwargs)
            if fetched_data:
                for field in fetched_data:
                    if field in self.fields:
                        self.fields[
                            field
                        ].help_text += " (valeur extraite de Index EgaPro)"
                        self.fields[field].disabled = True

    class BDESE1Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
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
                "pourcentage_masse_salariale_formation_continue",
                "montant_formation_continue",
                "nombre_heures_stage_remunerees",
                "nombre_heures_stage_non_remunerees",
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
                "pourcentage_temps_medecin_du_travail",
                "nombre_salaries_inaptes",
                "nombre_salaries_reclasses",
            ]

    class BDESE2Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
                "evolution_amortissement",
                "montant_depenses_recherche_developpement",
                "evolution_productivite",
            ]

    class BDESE3Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
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
                "nombre_promotions_homme",
                "nombre_promotions_femme",
                "duree_moyenne_entre_deux_promotions_homme",
                "duree_moyenne_entre_deux_promotions_femme",
                "anciennete_moyenne_homme",
                "anciennete_moyenne_femme",
                "anciennete_moyenne_dans_categorie_profesionnelle_homme",
                "anciennete_moyenne_dans_categorie_profesionnelle_femme",
                "age_moyen_homme",
                "age_moyen_femme",
                "remuneration_moyenne_homme",
                "remuneration_moyenne_femme",
                "remuneration_moyenne_par_age_homme",
                "remuneration_moyenne_par_age_femme",
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
                "complement_salaire_conge",
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
            ]

    class BDESE4Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
                "capitaux_propres",
                "emprunts_et_dettes_financieres",
                "impots_et_taxes",
            ]

    class BDESE5Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
                "frais_personnel",
                "evolution_salariale_par_categorie",
                "evolution_salariale_par_sexe",
                "salaire_base_minimum_par_categorie",
                "salaire_base_minimum_par_sexe",
                "salaire_moyen_par_categorie",
                "salaire_moyen_par_sexe",
                "salaire_median_par_categorie",
                "salaire_median_par_sexe",
                "rapport_masse_salariale_effectif_mensuel",
                "remuneration_moyenne_decembre",
                "remuneration_mensuelle_moyenne",
                "part_primes_non_mensuelle",
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
            ]

    class BDESE6Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
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
            ]

    class BDESE7Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = ["remuneration_actionnaires", "remuneration_actionnariat_salarie"]

    class BDESE8Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
                "aides_financieres",
                "reductions_impots",
                "exonerations_cotisations_sociales",
                "credits_impots",
                "mecenat",
                "chiffre_affaires",
                "benefices_ou_pertes",
                "resultats_globaux",
                "affectation_benefices",
            ]

    class BDESE9Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = ["partenariats_pour_produire", "partenariats_pour_beneficier"]

    class BDESE10Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = ["transferts_de_capitaux", "cessions_fusions_acquisitions"]

    class BDESE11Form(BDESEForm):
        class Meta:
            model = BDESEForm.Meta.model
            field_classes = BDESEForm.Meta.field_classes
            fields = [
                "informations_environnementales",
                "prevention_et_gestion_dechets",
                "bilan_gaz_effet_de_serre",
                "prise_en_compte_questions_environnementales",
                "quantite_de_dechets_dangereux",
                "consommation_eau",
                "consommation_energie",
                "postes_emissions_directes_gaz_effet_de_serre",
                "bilan_gaz_effet_de_serre",
            ]

    if step == 1:
        return BDESE1Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 2:
        return BDESE2Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 3:
        return BDESE3Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 4:
        return BDESE4Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 5:
        return BDESE5Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 6:
        return BDESE6Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 7:
        return BDESE7Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 8:
        return BDESE8Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 9:
        return BDESE9Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 10:
        return BDESE10Form(fetched_data, instance=instance, *args, **kwargs)
    elif step == 11:
        return BDESE11Form(fetched_data, instance=instance, *args, **kwargs)
    return BDESEForm(fetched_data, instance=instance, *args, **kwargs)
