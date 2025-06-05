import math
from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.forms.fields import validators
from django.utils.timezone import datetime
from django.utils.timezone import timezone

from .models import ActualisationCaracteristiquesAnnuelles
from .models import CaracteristiquesAnnuelles
from .models import Entreprise
from utils.forms import DateInput
from utils.forms import DsfrForm


ERREUR_CHAMP_MANQUANT_GROUPE = (
    "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
)
ERREUR_CHAMP_MANQUANT_COMPTES_CONSOLIDES = (
    "Ce champ est obligatoire lorsque les comptes sont consolidés"
)


class SirenField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get("label"):
            kwargs["label"] = "Votre numéro SIREN"
        if not kwargs.get("help_text"):
            kwargs[
                "help_text"
            ] = "Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises"
        kwargs["min_length"] = 9
        kwargs["max_length"] = 9
        super().__init__(*args, **kwargs)

    def validate(self, value):
        super().validate(value)
        try:
            int(value)
        except ValueError:
            raise ValidationError("Le siren est incorrect")


class EntrepriseAttachForm(DsfrForm):
    siren = SirenField()
    fonctions = forms.CharField(label="Fonction(s) dans la société")


class EntrepriseDetachForm(DsfrForm):
    siren = SirenField()


class EntrepriseForm(DsfrForm):
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

    def clean(self):
        super().clean()

        appartient_groupe = self.cleaned_data.get("appartient_groupe")
        if appartient_groupe:
            if not self.cleaned_data.get("effectif_groupe"):
                self.add_error("effectif_groupe", ERREUR_CHAMP_MANQUANT_GROUPE)
        else:
            self.cleaned_data["est_societe_mere"] = None
            self.cleaned_data["effectif_groupe"] = None
            self.cleaned_data["comptes_consolides"] = None

        comptes_consolides = self.cleaned_data.get("comptes_consolides")
        tranche_chiffre_affaires_consolide = self.cleaned_data.get(
            "tranche_chiffre_affaires_consolide"
        )
        tranche_bilan_consolide = self.cleaned_data.get("tranche_bilan_consolide")
        if comptes_consolides:
            if not tranche_chiffre_affaires_consolide:
                self.add_error(
                    "tranche_chiffre_affaires_consolide",
                    ERREUR_CHAMP_MANQUANT_COMPTES_CONSOLIDES,
                )
            if not tranche_bilan_consolide:
                self.add_error(
                    "tranche_bilan_consolide", ERREUR_CHAMP_MANQUANT_COMPTES_CONSOLIDES
                )
        else:
            if tranche_chiffre_affaires_consolide:
                self.cleaned_data["tranche_chiffre_affaires_consolide"] = None
            if tranche_bilan_consolide:
                self.cleaned_data["tranche_bilan_consolide"] = None

        effectif = self.cleaned_data.get("effectif")
        effectif_groupe = self.cleaned_data.get("effectif_groupe")
        if effectif and effectif_groupe and est_superieur(effectif, effectif_groupe):
            self.add_error(
                "effectif_groupe",
                "L'effectif du groupe ne peut pas être inférieur à l'effectif",
            )

        return self.cleaned_data


class EntrepriseQualificationForm(EntrepriseForm, forms.ModelForm):
    societe_mere_en_france = forms.BooleanField(
        required=False,
        label=Entreprise.societe_mere_en_france.field.verbose_name,
    )
    confirmation_naf = forms.CharField(
        label="Code NAF/APE",
        help_text="Merci de vérifier et confirmer le code APE de votre entreprise",
        validators=[validators.RegexValidator(regex=r"^\d{2}\.\d{1,2}[A-Z]$")],
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
            "effectif_groupe_permanent",
            "tranche_chiffre_affaires",
            "tranche_bilan",
            "tranche_chiffre_affaires_consolide",
            "tranche_bilan_consolide",
            "bdese_accord",
            "systeme_management_energie",
        ]
        labels = {
            "date_cloture_exercice": "Date de clôture du dernier exercice comptable",
            "systeme_management_energie": "L'entreprise a mis en place un <a target='_blank' href='https://agirpourlatransition.ademe.fr/entreprises/demarche-decarbonation-industrie/agir/structurer-demarche/mettre-en-place-systeme-management-energie'>système de management de l’énergie</a>",
        }
        help_texts = {
            "tranche_chiffre_affaires": "Montant net du chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Total du bilan de l'exercice clos",
        }
        widgets = {
            "bdese_accord": forms.CheckboxInput,
            "systeme_management_energie": forms.CheckboxInput,
            "date_cloture_exercice": DateInput,
        }

    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop("entreprise", None)

        super().__init__(*args, **kwargs)

        if entreprise:
            self.entreprise = entreprise
            self.fields["confirmation_naf"].initial = entreprise.code_NAF

        if "date_cloture_exercice" in self.initial and isinstance(
            self.initial["date_cloture_exercice"], date
        ):
            self.initial["date_cloture_exercice"] = self.initial[
                "date_cloture_exercice"
            ].isoformat()

    def clean(self):
        ERREUR_CHAMP_MANQUANT_GROUPE = (
            "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
        )

        super().clean()

        appartient_groupe = self.cleaned_data.get("appartient_groupe")
        effectif_groupe = self.cleaned_data.get("effectif_groupe")
        effectif_groupe_permanent = self.cleaned_data.get("effectif_groupe_permanent")
        effectif_groupe_france = self.cleaned_data.get("effectif_groupe_france")
        if appartient_groupe:
            if not effectif_groupe_permanent:
                self.add_error(
                    "effectif_groupe_permanent", ERREUR_CHAMP_MANQUANT_GROUPE
                )
            if not effectif_groupe_france:
                self.add_error("effectif_groupe_france", ERREUR_CHAMP_MANQUANT_GROUPE)
        else:
            self.cleaned_data["effectif_groupe_france"] = None
            self.cleaned_data["effectif_groupe_permanent"] = None
            self.cleaned_data["societe_mere_en_france"] = None

        effectif = self.cleaned_data.get("effectif")
        effectif_outre_mer = self.cleaned_data.get("effectif_outre_mer")
        if (
            effectif
            and effectif_outre_mer
            and est_superieur(effectif_outre_mer, effectif)
        ):
            self.add_error(
                "effectif_outre_mer",
                "L'effectif outre-mer ne peut pas être supérieur à l'effectif",
            )
        if (
            effectif_groupe
            and effectif_groupe_permanent
            and est_superieur(effectif_groupe_permanent, effectif_groupe)
        ):
            self.add_error(
                "effectif_groupe_permanent",
                "L'effectif permanent du groupe ne peut pas être supérieur à l'effectif du groupe international",
            )
        if (
            effectif_groupe
            and effectif_groupe_france
            and est_superieur(effectif_groupe_france, effectif_groupe)
        ):
            self.add_error(
                "effectif_groupe_france",
                "L'effectif du groupe France ne peut pas être supérieur à l'effectif du groupe international",
            )
        if (
            effectif
            and effectif_groupe_france
            and self.cleaned_data.get("est_societe_mere")
            and self.cleaned_data.get("societe_mere_en_france")
            and est_superieur(effectif, effectif_groupe_france)
        ):
            self.add_error(
                "effectif_groupe_france",
                "L'effectif du groupe France ne peut pas être inférieur à l'effectif si vous êtes la société mère du groupe et en France",
            )

        if not self.cleaned_data.get("est_interet_public"):
            self.cleaned_data["est_cotee"] = False

        return self.cleaned_data

    def _update_entreprise(self):
        if not self.entreprise:
            raise ValidationError("Entreprise incorrecte")

        self.entreprise.code_NAF = self.cleaned_data["confirmation_naf"]
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
        self.entreprise.save()

    def save(self, **_):
        # On remplace la procédure de sauvegarde de l'objet par une personnalisée
        # car il y a plusieurs étapes de constructions dans le modèle `Entreprise` :
        # la sauvegarde ne peut être effectuée directement à partir des champs du formulaire

        # et : normallement `save()` effectue un `clean()` avant d'effectuer des opérations en base
        # on peut éventuellement s'en passer ici, si on a testé au préalable la validité du formulaire (dans la vue),
        # mais dans le doute ...
        if self.errors:
            raise ValidationError(
                "Impossible de sauvegarder : le formulaire contient des erreurs."
            )

        self.entreprise.actualise_caracteristiques(
            ActualisationCaracteristiquesAnnuelles(
                date_cloture_exercice=self.cleaned_data["date_cloture_exercice"],
                effectif=self.cleaned_data["effectif"],
                effectif_securite_sociale=self.cleaned_data[
                    "effectif_securite_sociale"
                ],
                effectif_outre_mer=self.cleaned_data["effectif_outre_mer"],
                effectif_groupe=self.cleaned_data["effectif_groupe"],
                effectif_groupe_france=self.cleaned_data["effectif_groupe_france"],
                effectif_groupe_permanent=self.cleaned_data[
                    "effectif_groupe_permanent"
                ],
                tranche_chiffre_affaires=self.cleaned_data["tranche_chiffre_affaires"],
                tranche_bilan=self.cleaned_data["tranche_bilan"],
                tranche_chiffre_affaires_consolide=self.cleaned_data[
                    "tranche_chiffre_affaires_consolide"
                ],
                tranche_bilan_consolide=self.cleaned_data["tranche_bilan_consolide"],
                bdese_accord=self.cleaned_data["bdese_accord"],
                systeme_management_energie=self.cleaned_data[
                    "systeme_management_energie"
                ],
            )
        ).save()

        # un peu de ménage dans les caractéristiques annuelles obsolètes
        CaracteristiquesAnnuelles.objects.filter(
            entreprise=self.entreprise,
            annee__gt=self.cleaned_data["date_cloture_exercice"].year,
        ).delete()

        # enfin, on sauvegarde aussi les données de l'entreprise, le tout pour alléger la vue
        self._update_entreprise()


def est_superieur(effectif_1, effectif_2):
    borne_inferieure_1 = int(effectif_1.split("-")[0].strip("+"))
    try:
        borne_superieure_2 = int(effectif_2.split("-")[1])
    except IndexError:
        borne_superieure_2 = math.inf
    return borne_inferieure_1 > borne_superieure_2
