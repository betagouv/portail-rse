from dataclasses import dataclass
from dataclasses import field
from enum import Enum

import django.db.models as models


class ESRS(models.TextChoices):
    ESRS_1 = "ESRS_1"
    ESRS_2 = "ESRS_2"

    ESRS_E1 = "ESRS_E1"
    ESRS_E2 = "ESRS_E2"
    ESRS_E3 = "ESRS_E3"
    ESRS_E4 = "ESRS_E4"
    ESRS_E5 = "ESRS_E5"

    ESRS_S1 = "ESRS_S1"
    ESRS_S2 = "ESRS_S2"
    ESRS_S3 = "ESRS_S3"
    ESRS_S4 = "ESRS_S4"

    ESRS_G1 = "ESRS_G1"

    @classmethod
    def codes(cls):
        return (
            "E1",
            "E2",
            "E3",
            "E4",
            "E5",
            "S1",
            "S2",
            "S3",
            "S4",
            "G1",
        )


class ThemeESRS(Enum):
    ESRS_E1 = "environnement"
    ESRS_E2 = "environnement"
    ESRS_E3 = "environnement"
    ESRS_E4 = "environnement"
    ESRS_E5 = "environnement"
    ESRS_S1 = "social"
    ESRS_S2 = "social"
    ESRS_S3 = "social"
    ESRS_S4 = "social"
    ESRS_G1 = "gouvernance"


class TitreESRS(Enum):
    ESRS_E1 = "ESRS E1 - Changement climatique"
    ESRS_E2 = "ESRS E2 - Pollution"
    ESRS_E3 = "ESRS E3 - Eau et ressources marines"
    ESRS_E4 = "ESRS E4 - Biodiversité et écosystèmes"
    ESRS_E5 = "ESRS E5 - Utilisation des ressources et économie circulaire"
    ESRS_S1 = "ESRS S1 - Personnel de l'entreprise"
    ESRS_S2 = "ESRS S2 - Travailleurs de la chaîne de valeur"
    ESRS_S3 = "ESRS S3 - Communautés affectées"
    ESRS_S4 = "ESRS S4 - Consommateurs et utilisateurs finaux"
    ESRS_G1 = "ESRS G1 - Conduite des affaires"


@dataclass
class EnjeuNormalise:
    esrs: ESRS
    nom: str
    children: list["EnjeuNormalise"] = field(default_factory=list)
    description: str = ""


# proposition :
# enjeux ajoutés automatiquement à la création d'un nouveau rapport CSRD

ENJEUX_NORMALISES = [
    EnjeuNormalise(
        esrs=ESRS.ESRS_E1,
        nom="Adaptation au changement climatique",
        description="L’adaptation au changement climatique renvoie au processus d’adaptation de l’entreprise au changement climatique réel et attendu",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E1,
        nom="Atténuation du changement climatique",
        description="L’atténuation du changement climatique se réfère aux efforts de l’entreprise en faveur du processus général consistant à limiter l’élévation de la température moyenne de la planète à 1,5° C par rapport aux niveaux préindustriels, conformément à l’accord de Paris. La présente norme couvre les exigences de publication liées, notamment, aux sept gaz à effet de serre (GES) que sont le dioxyde de carbone (CO2), le méthane (CH4), le protoxyde d’azote (N2O), les hydrofluorocarbures (HFC), les hydrocarbures perfluorés (PFC), l’hexafluorure de soufre (SF6) et le trifluorure d’azote (NF3). Elle couvre également les exigences de publication portant sur la manière dont l’entreprise gère ses émissions de GES ainsi que les risques de transition qui y sont associés",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E1,
        nom="Énergie",
        description="Les exigences de publication relatives à l’« énergie » couvrent toutes les formes de production et de consommation d’énergie.",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E2,
        nom="Pollution de l'air",
        description="La « pollution de l’air » désigne les émissions dans l’air (air intérieur et air extérieur) dues à l’entreprise, ainsi que la prévention et la réduction de ces émissions",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E2,
        nom="Pollution des eaux",
        description="La « pollution de l’eau » désigne les rejets dans l’eau dus à l’entreprise, ainsi que la prévention et la réduction de ces émissions.",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E2,
        nom="Pollution des sols",
        description="La « pollution des sols » désigne les rejets dans le sol dus à l’entreprise ainsi que là prévention et la réduction de ces émission.",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E2,
        nom="Substances préoccupantes",
        description="En ce qui concerne les « substances préoccupantes », la présente norme couvre la production, l’utilisation, la distribution et la commercialisation, par l’entreprise, de substances préoccupante",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E2,
        nom="Substances extrêmement préoccupantes",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E2,
        nom="Microplastiques",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E3,
        nom="Eau",
        description="Par « eau », on entend que la présente norme couvre les eaux de surface, les eaux souterraines. Elle inclut des exigences de publication relatives à la consommation d’eau dans les activités, produits et services de l’entreprise, ainsi que des informations connexes sur les prélèvements et rejets d’eau.",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E3,
        nom="Ressources marines",
        description="Par « ressources marines », on entend que la présente norme couvre l’extraction et l’utilisation de ces ressources, ainsi que les activités économiques s’y rapportant.",
        children=[
            EnjeuNormalise(
                esrs=ESRS.ESRS_E3,
                nom="Consommation d'eau",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_E3,
                nom="Prélèvements d'eau",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_E3,
                nom="Rejet des eaux",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_E3,
                nom="Rejet des eaux dans les océans",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_E3,
                nom="Extraction et utilisation des ressources marines",
            ),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E4,
        nom="Vecteurs directs de perte de biodiversité",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_E4, nom="Changement climatique"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_E4,
                nom="Changement d’affectation des terres, changement d’utilisation de l’eau douce et des mers",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_E4, nom="Exploitation directe"),
            EnjeuNormalise(esrs=ESRS.ESRS_E4, nom="Espèces exotiques envahissantes"),
            EnjeuNormalise(esrs=ESRS.ESRS_E4, nom="Pollution"),
            EnjeuNormalise(esrs=ESRS.ESRS_E4, nom="Autres"),
        ],
    ),
    EnjeuNormalise(esrs=ESRS.ESRS_E4, nom="Incidence sur l'état des espèces"),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E4, nom="Incidence sur l'étendue et l'état des écosystèmes"
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E5,
        nom="Ressources entrantes, y compris l’utilisation des ressources",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E5,
        nom="Ressources sortantes liées aux produits et services",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_E5,
        nom="Déchets",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S1,
        nom="Conditions de travail",
        description="Par exemple, en matière d’égalité des chances, la discrimination à l’embauche et à la promotion à l’égard des femmes peut réduire l’accès de l’entreprise à une main-d’œuvre qualifiée et nuire à sa réputation. À l’inverse, les politiques visant à accroître la représentation des femmes au sein des effectifs et aux niveaux supérieurs de l’encadrement peuvent avoir des incidences positives, telles que l’expansion de la réserve de main-d’œuvre qualifiée et l’amélioration de l’image de marque de l’entreprise.",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Sécurité de l'emploi"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Temps de travail",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Salaires décents"),
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Dialogue social"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Liberté d'association, existence de comités d'entreprise et droits des travailleurs à l'information, à la consultation et à la participation",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Négociation collective, y compris la proportion de travailleurs couverts par des conventions collectives",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Equilibre entre vie professionnelle et vie privée",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Santé et sécurité"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S1,
        nom="Égalité de traitement et égalité des chances pour tous",
        children=[
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Egalité de genre et égalité de rémunération pour un travail de valeur égale",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Formation et développement des compétences",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1, nom="Emploi et inclusion des personnes handicapées"
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Mesures de lutte contre la violence et le harcèlement sur le lieu de travail",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Diversité"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S1,
        nom="Autres droits liés au travail",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Travail des enfants"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S1,
                nom="Travail forcé",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Logement adéquat"),
            EnjeuNormalise(esrs=ESRS.ESRS_S1, nom="Protection de la vie privée"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S2,
        nom="Conditions de travail",
        description="Par exemple, sécurité de l’emploi, temps de travail, salaire décent, dialogue social, liberté d’association, y compris l’existence de comités d’entreprise, négociation collective, équilibre entre vie professionnelle et vie privée, et santé et sécurité",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Sécurité de l'emploi"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Temps de travail",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Salaires décents"),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Dialogue social"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Liberté d'association y compris l'existence de comités d'entreprise",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Négociation collective"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Equilibre entre vie professionnelle et vie privée",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Santé et sécurité"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S2,
        nom="Égalité de traitement et égalité des chances pour tous",
        description="Par exemple, égalité de genre et égalité de rémunération pour un travail de valeur égale, formation et développement des compétences, emploi et inclusion des personnes handicapées, mesures de lutte contre la violence et le harcèlement sur le lieu de travail, et diversité",
        children=[
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Egalité de genre et égalité de rémunération pour un travail de valeur égale",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Formation et développement des compétences",
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2, nom="Emploi et inclusion des personnes handicapées"
            ),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Mesures de lutte contre la violence et le harcèlement sur le lieu de travail",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Diversité"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S2,
        nom="Autres droits liés au travail",
        description="Par exemple, travail des enfants, travail forcé, logement adéquat, eau et assainissement, et protection de la vie privée",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Travail des enfants"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S2,
                nom="Travail forcé",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Logement adéquat"),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Eau et assainissement"),
            EnjeuNormalise(esrs=ESRS.ESRS_S2, nom="Protection de la vie privée"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S3,
        nom="Droits économiques, sociaux et culturels des communautés ",
        description="Par exemple, logement adéquat, alimentation adéquate, eau et assainissement, incidences liées à la terre et à la sécurité",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Logement adéquat"),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Alimentation adéquate"),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Eau et assainissement"),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Incidences liées à la terre"),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Incidences liées à la sécurité"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S3,
        nom="Droits civils et politiques des communautés",
        description="Par exemple, liberté d’expression, liberté de réunion, incidences sur les défenseurs des droits de l’homme",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Liberté d’expression"),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Liberté de réunion"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S3,
                nom="Incidences sur les défenseurs des droits de l’homme",
            ),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S3,
        nom="Droits particuliers des peuples autochtones",
        description="Par exemple, consentement préalable, donné librement et en connaissance de cause, autodétermination, droits culturels",
        children=[
            EnjeuNormalise(
                esrs=ESRS.ESRS_S3,
                nom="Consentement préalable, donné librement et en connaissance de cause",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Auto-détermination"),
            EnjeuNormalise(esrs=ESRS.ESRS_S3, nom="Droits culturels"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S4,
        nom="Incidences liées aux informations sur les consommateurs et/ou les utilisateurs finals",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Protection de la vie privée"),
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Liberté d’expression"),
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Accès à l’information (de qualité)"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S4,
        nom="Sécurité des consommateurs et/ou des utilisateurs finals",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Santé et sécurité"),
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Sécurité de la personne"),
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Protection des enfants"),
        ],
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_S4,
        nom="Inclusion sociale des consommateurs et/ou des utilisateurs finals",
        children=[
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Non-discrimination"),
            EnjeuNormalise(esrs=ESRS.ESRS_S4, nom="Accès aux produits et services"),
            EnjeuNormalise(
                esrs=ESRS.ESRS_S4, nom="Pratiques de commercialisation responsables"
            ),
        ],
    ),
    EnjeuNormalise(esrs=ESRS.ESRS_G1, nom="Culture d’entreprise"),
    EnjeuNormalise(esrs=ESRS.ESRS_G1, nom="Protection des lanceurs d’alerte"),
    EnjeuNormalise(esrs=ESRS.ESRS_G1, nom="Bien-être animal"),
    EnjeuNormalise(esrs=ESRS.ESRS_G1, nom="Engagement politique"),
    EnjeuNormalise(
        esrs=ESRS.ESRS_G1,
        nom="Gestion des relations avec les fournisseurs, y compris les pratiques en matière de paiement",
    ),
    EnjeuNormalise(
        esrs=ESRS.ESRS_G1,
        nom="Corruption et versement de pots-de-vin",
        children=[
            EnjeuNormalise(
                esrs=ESRS.ESRS_G1,
                nom="Prévention et détection, y compris les formations",
            ),
            EnjeuNormalise(esrs=ESRS.ESRS_G1, nom="Incidents/Cas"),
        ],
    ),
]


@dataclass
class EtapeCSRD:
    id: str
    nom: str
    sous_etapes: dict = field(default_factory=dict)
    ETAPES_VALIDABLES = [
        "introduction",
        # l'étape "analyse de la double matérialité" contient deux sous-étapes :
        "selection-enjeux",
        "analyse-materialite",
        # l'étape "collecte des données" contient deux sous-étapes :
        "selection-informations",
        "analyse-ecart",
        "redaction-rapport-durabilite",
    ]

    @classmethod
    def id_suivant(cls, id_etape):
        for index, id in enumerate(cls.ETAPES_VALIDABLES):
            if id == id_etape:
                return cls.ETAPES_VALIDABLES[index + 1]

    @classmethod
    def get(cls, id_etape):
        for etape in ETAPES_CSRD:
            if etape.id == id_etape:
                return etape
            for sous_etape in etape.sous_etapes:
                if sous_etape.id == id_etape:
                    return sous_etape
        raise Exception(f"Étape CSRD inconnue : {id_etape}")

    @classmethod
    def id_etape_est_validee(cls, id_etape_reference, id_etape_a_tester):
        return cls.ETAPES_VALIDABLES.index(
            id_etape_reference
        ) <= cls.ETAPES_VALIDABLES.index(id_etape_a_tester)

    @classmethod
    def progression_id_etape(cls, id_etape):
        max = len(cls.ETAPES_VALIDABLES) - 1  # l'étape introduction est ignorée
        if id_etape:
            actuel = cls.ETAPES_VALIDABLES.index(id_etape)
        else:
            actuel = 0
        pourcent = int(actuel / max * 100)
        return {"max": max, "actuel": actuel, "pourcent": pourcent}


phase2 = EtapeCSRD(
    id="collection-donnees",
    nom="Collecter les données de son entreprise",
    sous_etapes=[
        EtapeCSRD(
            id="selection-informations",
            nom="Analyser la matérialité des informations élémentaires",
        ),
        EtapeCSRD(
            id="analyse-ecart",
            nom="Réaliser une analyse d’écart",
        ),
    ],
)

ETAPES_CSRD = [
    EtapeCSRD(id="introduction", nom="Introduction"),
    EtapeCSRD(
        id="analyse-double-mat",
        nom="Analyser la double matérialité",
        sous_etapes=[
            EtapeCSRD(
                id="selection-enjeux", nom="Identifier la liste de ses enjeux ESG"
            ),
            EtapeCSRD(
                id="analyse-materialite", nom="Sélectionner les enjeux ESG matériels"
            ),
        ],
    ),
    phase2,
    EtapeCSRD(
        id="redaction-rapport-durabilite",
        nom="Rédiger son rapport de durabilité",
    ),
]
