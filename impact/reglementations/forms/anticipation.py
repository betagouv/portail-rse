from datetime import date
from datetime import datetime

from django import forms
from django.utils.timezone import timezone

from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from utils.forms import DateInput
from utils.forms import DsfrForm


class AnticipationForm(DsfrForm, forms.ModelForm):
    est_cotee = forms.BooleanField(
        required=False,
        label=Entreprise.est_cotee.field.verbose_name,
    )
    est_interet_public = forms.BooleanField(
        required=False,
        label=Entreprise.est_interet_public.field.verbose_name,
        help_text=Entreprise.est_interet_public.field.help_text,
    )
    appartient_groupe = forms.BooleanField(
        required=False,
        label="L'entreprise fait partie d'un groupe composé d'une société-mère et d'une ou plusieurs filiales",
    )
    est_societe_mere = forms.BooleanField(
        required=False,
        label=Entreprise.est_societe_mere.field.verbose_name,
    )
    comptes_consolides = forms.BooleanField(
        required=False,
        label="Le groupe d'entreprises établit des comptes consolidés",
    )

    societe_mere_en_france = forms.BooleanField(
        required=False,
        label=Entreprise.societe_mere_en_france.field.verbose_name,
    )

    class Meta:
        model = CaracteristiquesAnnuelles
        fields = [
            "date_cloture_exercice",
            "effectif",
            "effectif_securite_sociale",
            "effectif_outre_mer",
            "effectif_groupe",
            "effectif_groupe_france",
            "tranche_chiffre_affaires",
            "tranche_bilan",
            "tranche_chiffre_affaires_consolide",
            "tranche_bilan_consolide",
            "bdese_accord",
            "tranche_consommation_energie_finale",
        ]
        labels = {
            "date_cloture_exercice": "Date de clôture du dernier exercice comptable",
        }
        help_texts = {
            "tranche_chiffre_affaires": "Montant net du chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Total du bilan de l'exercice clos",
            "tranche_consommation_energie_finale": "La consommation annuelle moyenne d'énergie finale correspond à la moyenne de vos consommations sur les 3 dernières années civiles complètes, toutes sources confondues : électricité, gaz, fioul, chaleur réseau, et carburants de votre flotte de véhicules. Vous pouvez retrouver ces données sur vos factures énergétiques, auprès de vos gestionnaires de réseau (Enedis pour l'électricité, GRDF pour le gaz), et via vos relevés de cartes carburant. Le calcul s'effectue au niveau de votre SIREN (ensemble de vos sites et véhicules).",
        }
        widgets = {
            "bdese_accord": forms.CheckboxInput,
            "date_cloture_exercice": DateInput,
        }

    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop("entreprise", None)

        super().__init__(*args, **kwargs)

        if entreprise:
            self.entreprise = entreprise

        if "date_cloture_exercice" in self.initial and isinstance(
            self.initial["date_cloture_exercice"], date
        ):
            self.initial["date_cloture_exercice"] = self.initial[
                "date_cloture_exercice"
            ].isoformat()

    def save(self, *args, **kwargs):
        """pas d'enregistrement pour l'expérimentation des utilisateurs

        Cette méthode n'est jamais appelée mais est définie pour rendre explicite l'intention.
        """

    def caracteristiques_anticipees(self):
        if self.errors:
            raise ValidationError(
                "Impossible de sauvegarder : le formulaire contient des erreurs."
            )

        caracs = ActualisationCaracteristiquesAnnuelles(
            date_cloture_exercice=self.cleaned_data["date_cloture_exercice"],
            effectif=self.cleaned_data["effectif"],
            effectif_securite_sociale=self.cleaned_data["effectif_securite_sociale"],
            effectif_outre_mer=self.cleaned_data["effectif_outre_mer"],
            effectif_groupe=self.cleaned_data["effectif_groupe"],
            effectif_groupe_france=self.cleaned_data["effectif_groupe_france"],
            tranche_chiffre_affaires=self.cleaned_data["tranche_chiffre_affaires"],
            tranche_bilan=self.cleaned_data["tranche_bilan"],
            tranche_chiffre_affaires_consolide=self.cleaned_data[
                "tranche_chiffre_affaires_consolide"
            ],
            tranche_bilan_consolide=self.cleaned_data["tranche_bilan_consolide"],
            bdese_accord=self.cleaned_data["bdese_accord"],
            tranche_consommation_energie_finale=self.cleaned_data[
                "tranche_consommation_energie_finale"
            ],
        )
        caracs.entreprise = self._entreprise_anticipee()
        return caracs

    def _entreprise_anticipee(self):
        if not self.entreprise:
            raise ValidationError("Entreprise incorrecte")

        self.entreprise.date_cloture_exercice = self.cleaned_data[
            "date_cloture_exercice"
        ]
        self.entreprise.est_cotee = self.cleaned_data["est_cotee"]
        self.entreprise.est_interet_public = self.cleaned_data["est_interet_public"]
        self.entreprise.appartient_groupe = self.cleaned_data["appartient_groupe"]
        self.entreprise.est_societe_mere = self.cleaned_data["est_societe_mere"]
        self.entreprise.societe_mere_en_france = self.cleaned_data[
            "societe_mere_en_france"
        ]
        self.entreprise.comptes_consolides = self.cleaned_data["comptes_consolides"]
        self.entreprise.date_derniere_qualification = datetime.now(tz=timezone.utc)
