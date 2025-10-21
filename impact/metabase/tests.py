from datetime import date
from datetime import datetime
from datetime import timezone

import pytest
from django.conf import settings
from django.core.management import call_command
from freezegun import freeze_time

from conftest import CODE_NAF_CEREALES
from conftest import CODE_PAYS_PORTUGAL
from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import Habilitation
from invitations.models import Invitation
from metabase.models import BDESE as MetabaseBDESE
from metabase.models import BGES as MetabaseBGES
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.models import Habilitation as MetabaseHabilitation
from metabase.models import IndexEgaPro as MetabaseIndexEgaPro
from metabase.models import Invitation as MetabaseInvitation
from metabase.models import Stats as MetabaseStats
from metabase.models import Utilisateur as MetabaseUtilisateur
from metabase.models import VSME as MetabaseVSME
from reglementations.models import BDESE_50_300
from reglementations.models import derniere_annee_a_remplir_bdese
from reglementations.tests.conftest import bdese_factory  # noqa
from vsme.models import EXIGENCES_DE_PUBLICATION
from vsme.models import RapportVSME

METABASE_DATABASE_NAME = settings.METABASE_DATABASE_NAME


def mark_bdese_as_complete(bdese):
    for step in bdese.STEPS:
        bdese.mark_step_as_complete(step)
    bdese.save()


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_qualifiee_sans_groupe(
    entreprise_factory, date_cloture_dernier_exercice
):
    date_creation = datetime(
        date_cloture_dernier_exercice.year,
        date_cloture_dernier_exercice.month,
        date_cloture_dernier_exercice.day,
        tzinfo=timezone.utc,
    )
    date_deuxieme_evolution = datetime(
        date_cloture_dernier_exercice.year + 1,
        date_cloture_dernier_exercice.month,
        date_cloture_dernier_exercice.day,
        tzinfo=timezone.utc,
    )
    date_troisieme_evolution = datetime(
        date_cloture_dernier_exercice.year + 2,
        date_cloture_dernier_exercice.month,
        date_cloture_dernier_exercice.day,
        tzinfo=timezone.utc,
    )
    date_derniere_qualification = date(
        date_cloture_dernier_exercice.year,
        month=12,
        day=15,
    )
    with freeze_time(date_creation) as frozen_datetime:
        entreprise = entreprise_factory(
            siren="000000001",
            denomination="Entreprise A",
            date_cloture_exercice=date_cloture_dernier_exercice,
            date_derniere_qualification=date_derniere_qualification,
            categorie_juridique_sirene=5699,
            code_pays_etranger_sirene=CODE_PAYS_PORTUGAL,
            code_NAF=CODE_NAF_CEREALES,
            effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
            effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
            est_cotee=False,
            est_interet_public=False,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
            bdese_accord=False,
            systeme_management_energie=False,
        )
        frozen_datetime.move_to(date_deuxieme_evolution)
        actualisation = ActualisationCaracteristiquesAnnuelles(
            date_cloture_exercice=date_cloture_dernier_exercice.replace(
                year=date_cloture_dernier_exercice.year + 1
            ),
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
            effectif_groupe=None,
            effectif_groupe_france=None,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
            tranche_chiffre_affaires_consolide=None,
            tranche_bilan_consolide=None,
            bdese_accord=True,
            systeme_management_energie=False,
        )
        entreprise.actualise_caracteristiques(actualisation).save()
        frozen_datetime.move_to(date_troisieme_evolution)
        actualisation = ActualisationCaracteristiquesAnnuelles(
            date_cloture_exercice=date_cloture_dernier_exercice.replace(
                year=date_cloture_dernier_exercice.year + 2
            ),
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
            effectif_groupe=None,
            effectif_groupe_france=None,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            tranche_chiffre_affaires_consolide=None,
            tranche_bilan_consolide=None,
            bdese_accord=True,
            systeme_management_energie=True,
        )
        entreprise.actualise_caracteristiques(actualisation).save()

    call_command("sync_metabase")

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.pk == metabase_entreprise.impact_id == entreprise.pk
    assert metabase_entreprise.ajoutee_le == date_creation
    assert metabase_entreprise.modifiee_le == date_troisieme_evolution
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.denomination == "Entreprise A"
    assert metabase_entreprise.categorie_juridique == "SOCIETE_ANONYME"
    assert metabase_entreprise.pays == "Portugal"
    assert metabase_entreprise.code_NAF == CODE_NAF_CEREALES
    assert (
        metabase_entreprise.date_cloture_exercice
        == date_cloture_dernier_exercice.replace(
            year=date_cloture_dernier_exercice.year + 2
        )
    )
    assert (
        metabase_entreprise.date_derniere_qualification == date_derniere_qualification
    )
    assert metabase_entreprise.est_cotee is False
    assert metabase_entreprise.est_interet_public is False
    assert metabase_entreprise.appartient_groupe is False
    assert metabase_entreprise.societe_mere_en_france is False
    assert metabase_entreprise.comptes_consolides is False
    assert metabase_entreprise.effectif == "300-499"
    assert metabase_entreprise.effectif_securite_sociale == "50-249"
    assert metabase_entreprise.effectif_outre_mer == "0-249"
    assert metabase_entreprise.effectif_groupe is None
    assert metabase_entreprise.tranche_bilan == "43M-100M"
    assert metabase_entreprise.tranche_chiffre_affaires == "50M-100M"
    assert metabase_entreprise.tranche_bilan_consolide is None
    assert metabase_entreprise.tranche_chiffre_affaires_consolide is None
    assert metabase_entreprise.bdese_accord is True
    assert metabase_entreprise.systeme_management_energie is True
    assert metabase_entreprise.nombre_utilisateurs == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_qualifiee_appartenant_a_un_groupe(
    entreprise_factory,
):
    entreprise_factory(
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M,
    )

    call_command("sync_metabase")

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.appartient_groupe
    assert metabase_entreprise.est_societe_mere
    assert metabase_entreprise.societe_mere_en_france
    assert metabase_entreprise.comptes_consolides
    assert (
        metabase_entreprise.effectif_groupe
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        metabase_entreprise.effectif_groupe_france
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        metabase_entreprise.tranche_chiffre_affaires_consolide
        == CaracteristiquesAnnuelles.CA_MOINS_DE_60M
    )
    assert (
        metabase_entreprise.tranche_bilan_consolide
        == CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M
    )


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_plusieurs_fois(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise A",
    )

    call_command("sync_metabase")
    call_command("sync_metabase")

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.impact_id == entreprise.pk
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.denomination == "Entreprise A"


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_sans_caracteristiques_annuelles():
    entreprise = Entreprise.objects.create(
        siren="000000001", denomination="Entreprise SAS"
    )

    call_command("sync_metabase")

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.denomination == "Entreprise SAS"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.date_cloture_exercice is None
    assert metabase_entreprise.effectif is None
    assert metabase_entreprise.effectif_securite_sociale is None
    assert metabase_entreprise.effectif_groupe is None
    assert metabase_entreprise.tranche_chiffre_affaires is None
    assert metabase_entreprise.tranche_bilan is None
    assert metabase_entreprise.bdese_accord is None
    assert metabase_entreprise.systeme_management_energie is None


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_sans_caracteristiques_qualifiantes(
    entreprise_factory,
):
    # Ce cas arrive lorsqu'on ajoute une nouvelle caracteristique qualifiante dans les caracteristiques annuelles
    # Les anciennes caracteristiques ne sont plus qualifiantes mais on veut quand même les avoir dans metabase
    entreprise = entreprise_factory()
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    tranche_bilan = caracteristiques.tranche_bilan
    caracteristiques.tranche_chiffre_affaires = None
    caracteristiques.save()

    call_command("sync_metabase")

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.tranche_bilan == tranche_bilan
    assert metabase_entreprise.tranche_chiffre_affaires is None


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_avec_un_utilisateur(
    entreprise_factory, django_user_model
):
    entreprise = entreprise_factory()
    utilisateur = django_user_model.objects.create(
        prenom="Alice",
        nom="Cooper",
        email="alice@portail-rse.test",
        reception_actualites=False,
        is_email_confirmed=True,
    )
    habilitation = Habilitation.ajouter(entreprise, utilisateur, fonctions="Présidente")

    call_command("sync_metabase")

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.nombre_utilisateurs == 1

    assert MetabaseUtilisateur.objects.count() == 1
    metabase_utilisateur = MetabaseUtilisateur.objects.first()
    assert metabase_utilisateur.pk == metabase_utilisateur.impact_id == utilisateur.pk
    assert metabase_utilisateur.ajoute_le == utilisateur.created_at
    assert metabase_utilisateur.modifie_le == utilisateur.updated_at
    assert metabase_utilisateur.connecte_le == utilisateur.last_login
    assert metabase_utilisateur.reception_actualites is False
    assert metabase_utilisateur.email_confirme is True
    assert metabase_utilisateur.nombre_entreprises == 1

    assert MetabaseHabilitation.objects.count() == 1
    metabase_habilitation = MetabaseHabilitation.objects.first()
    assert (
        metabase_habilitation.pk == metabase_habilitation.impact_id == habilitation.pk
    )
    assert metabase_habilitation.ajoutee_le == habilitation.created_at
    assert metabase_habilitation.modifiee_le == habilitation.updated_at
    assert metabase_habilitation.utilisateur == metabase_utilisateur
    assert metabase_habilitation.entreprise == metabase_entreprise
    assert metabase_habilitation.fonctions == "Présidente"
    assert not metabase_habilitation.confirmee_le

    date_confirmation = datetime.now()
    habilitation.confirmed_at = date_confirmation
    habilitation.save()

    call_command("sync_metabase")

    assert MetabaseHabilitation.objects.count() == 1
    metabase_habilitation = MetabaseHabilitation.objects.first()

    assert metabase_habilitation.confirmee_le.date() == date_confirmation.date()


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_nouvelle_entreprise_creee_entre_la_synchronisation_des_entreprises_et_des_utilisateurs(
    entreprise_factory, alice
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice)

    call_command("sync_metabase", entreprises=True)

    assert MetabaseEntreprise.objects.count() == 1

    nouvelle_entreprise = entreprise_factory(siren="000000002")
    Habilitation.ajouter(nouvelle_entreprise, alice)

    call_command("sync_metabase", entreprises=False, utilisateurs=True)

    # La nouvelle entreprise et la nouvelle habilitation ont été ignorées pour ne pas provoquer d'erreurs d'intégrité
    assert MetabaseEntreprise.objects.count() == 1
    assert MetabaseHabilitation.objects.count() == 1


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_invitations(entreprise_factory, alice, django_user_model):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice)
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email="bob@portail-rse.test",
        role="proprietaire",
        inviteur=alice,
    )

    call_command("sync_metabase")

    assert MetabaseInvitation.objects.count() == 1

    metabase_invitation = MetabaseInvitation.objects.first()
    metabase_utilisateur = MetabaseUtilisateur.objects.first()
    metabase_entreprise = MetabaseEntreprise.objects.first()

    assert metabase_invitation.pk == metabase_invitation.impact_id == invitation.pk
    assert metabase_invitation.ajoutee_le == invitation.created_at
    assert metabase_invitation.modifiee_le == invitation.updated_at
    assert metabase_invitation.inviteur == metabase_utilisateur
    assert metabase_invitation.entreprise == metabase_entreprise
    assert metabase_invitation.role == "proprietaire"
    assert not metabase_invitation.date_acceptation

    # L'invitation est acceptée par Bob
    bob = django_user_model.objects.create(
        prenom="Bob",
        nom="Dylan",
        email="bob@portail-rse.test",
    )
    invitation.accepter(bob)

    call_command("sync_metabase")

    metabase_invitation.refresh_from_db()
    assert metabase_invitation.date_acceptation
    assert MetabaseHabilitation.objects.get(invitation=metabase_invitation)


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_reglementations_BDESE(
    alice, entreprise_factory, bdese_factory, mock_api_egapro
):
    entreprise_non_soumise = entreprise_factory(
        siren="000000001", effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    entreprise_soumise_a_actualiser = entreprise_factory(
        siren="000000002", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    entreprise_soumise_en_cours = entreprise_factory(
        siren="000000003", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    entreprise_soumise_a_jour = entreprise_factory(
        siren="000000004", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    for entreprise in (
        entreprise_non_soumise,
        entreprise_soumise_a_actualiser,
        entreprise_soumise_en_cours,
        entreprise_soumise_a_jour,
    ):
        Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    bdese_en_cours = bdese_factory(
        bdese_class=BDESE_50_300,
        entreprise=entreprise_soumise_en_cours,
        annee=derniere_annee_a_remplir_bdese(),
    )
    bdese_a_jour = bdese_factory(
        bdese_class=BDESE_50_300,
        entreprise=entreprise_soumise_a_jour,
        annee=derniere_annee_a_remplir_bdese(),
    )
    mark_bdese_as_complete(bdese_a_jour)

    call_command("sync_metabase")

    assert MetabaseBDESE.objects.count() == 4

    metabase_bdese_entreprise_non_soumise = MetabaseBDESE.objects.get(
        entreprise__siren=entreprise_non_soumise.siren
    )
    assert not metabase_bdese_entreprise_non_soumise.est_soumise
    assert metabase_bdese_entreprise_non_soumise.statut is None

    metabase_bdese_entreprise_soumise_a_actualiser = MetabaseBDESE.objects.get(
        entreprise__siren=entreprise_soumise_a_actualiser.siren
    )
    assert metabase_bdese_entreprise_soumise_a_actualiser.est_soumise
    assert (
        metabase_bdese_entreprise_soumise_a_actualiser.statut
        == MetabaseBDESE.STATUT_A_ACTUALISER
    )

    metabase_bdese_entreprise_soumise_en_cours = MetabaseBDESE.objects.get(
        entreprise__siren=entreprise_soumise_en_cours.siren
    )
    assert metabase_bdese_entreprise_soumise_en_cours.est_soumise
    assert (
        metabase_bdese_entreprise_soumise_en_cours.statut
        == MetabaseBDESE.STATUT_EN_COURS
    )

    metabase_bdese_entreprise_soumise_a_jour = MetabaseBDESE.objects.get(
        entreprise__siren=entreprise_soumise_a_jour.siren
    )
    assert metabase_bdese_entreprise_soumise_a_jour.est_soumise
    assert (
        metabase_bdese_entreprise_soumise_a_jour.statut == MetabaseBDESE.STATUT_A_JOUR
    )


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_reglementations_IndexEgaPro(
    alice, entreprise_factory, mock_api_egapro
):
    entreprise_non_soumise = entreprise_factory(
        siren="000000001", effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    entreprise_soumise_a_actualiser = entreprise_factory(
        siren="000000002", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    entreprise_soumise_a_jour = entreprise_factory(
        siren="000000003", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    for entreprise in (
        entreprise_non_soumise,
        entreprise_soumise_a_actualiser,
        entreprise_soumise_a_jour,
    ):
        Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    mock_api_egapro.side_effect = [False, True]

    call_command("sync_metabase")

    assert mock_api_egapro.call_count == 2
    assert MetabaseIndexEgaPro.objects.count() == 3

    metabase_index_egapro_entreprise_non_soumise = MetabaseIndexEgaPro.objects.get(
        entreprise__siren=entreprise_non_soumise.siren
    )
    assert not metabase_index_egapro_entreprise_non_soumise.est_soumise
    assert metabase_index_egapro_entreprise_non_soumise.statut is None

    metabase_index_egapro_entreprise_soumise_a_actualiser = (
        MetabaseIndexEgaPro.objects.get(
            entreprise__siren=entreprise_soumise_a_actualiser.siren
        )
    )
    assert metabase_index_egapro_entreprise_soumise_a_actualiser.est_soumise
    assert (
        metabase_index_egapro_entreprise_soumise_a_actualiser.statut
        == MetabaseIndexEgaPro.STATUT_A_ACTUALISER
    )

    metabase_index_egapro_entreprise_soumise_a_jour = MetabaseIndexEgaPro.objects.get(
        entreprise__siren=entreprise_soumise_a_jour.siren
    )
    assert metabase_index_egapro_entreprise_soumise_a_jour.est_soumise
    assert (
        metabase_index_egapro_entreprise_soumise_a_jour.statut
        == MetabaseIndexEgaPro.STATUT_A_JOUR
    )


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_reglementations_BGES(
    alice, entreprise_factory, mock_api_egapro, mock_api_bges
):
    entreprise_non_soumise = entreprise_factory(
        siren="000000001", effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    entreprise_soumise_a_actualiser = entreprise_factory(
        siren="000000002", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
    )
    entreprise_soumise_a_jour = entreprise_factory(
        siren="000000003", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
    )
    for entreprise in (
        entreprise_non_soumise,
        entreprise_soumise_a_actualiser,
        entreprise_soumise_a_jour,
    ):
        Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    mock_api_bges.side_effect = [2010, 2023]

    with freeze_time("2023-12-20"):
        call_command("sync_metabase")

    assert mock_api_bges.call_count == 2
    assert MetabaseBGES.objects.count() == 3

    metabase_bges_entreprise_non_soumise = MetabaseBGES.objects.get(
        entreprise__siren=entreprise_non_soumise.siren
    )
    assert not metabase_bges_entreprise_non_soumise.est_soumise
    assert metabase_bges_entreprise_non_soumise.statut is None

    metabase_bges_entreprise_soumise_a_actualiser = MetabaseBGES.objects.get(
        entreprise__siren=entreprise_soumise_a_actualiser.siren
    )
    assert metabase_bges_entreprise_soumise_a_actualiser.est_soumise
    assert (
        metabase_bges_entreprise_soumise_a_actualiser.statut
        == MetabaseBGES.STATUT_A_ACTUALISER
    )

    metabase_bges_entreprise_soumise_a_jour = MetabaseBGES.objects.get(
        entreprise__siren=entreprise_soumise_a_jour.siren
    )
    assert metabase_bges_entreprise_soumise_a_jour.est_soumise
    assert metabase_bges_entreprise_soumise_a_jour.statut == MetabaseBGES.STATUT_A_JOUR


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_rapports_VSME(alice, entreprise_factory, mock_api_egapro):
    entreprise_sans_vsme = entreprise_factory(siren="000000001", utilisateur=alice)
    entreprise_avec_vsme_vide = entreprise_factory(siren="000000002", utilisateur=alice)
    entreprise_avec_vsme_commencee = entreprise_factory(
        siren="000000003", utilisateur=alice
    )
    entreprise_avec_vsme_terminee = entreprise_factory(
        siren="000000004", utilisateur=alice
    )

    vsme_vide = RapportVSME.objects.create(
        entreprise=entreprise_avec_vsme_vide, annee=2024
    )
    vsme_commencee = RapportVSME.objects.create(
        entreprise=entreprise_avec_vsme_commencee, annee=2024
    )
    vsme_terminee = RapportVSME.objects.create(
        entreprise=entreprise_avec_vsme_terminee, annee=2024
    )

    vsme_commencee.indicateurs.create(
        schema_id="B1-24-a", data={"yolo": "yolo"}  # indicateur réel de B1
    )

    EXIGENCES_REMPLISSABLES = [
        exigence
        for exigence in EXIGENCES_DE_PUBLICATION.values()
        if exigence.remplissable
    ]
    for exigence in EXIGENCES_REMPLISSABLES:
        for indicateur in exigence.load_json_schema():
            vsme_terminee.indicateurs.create(
                schema_id=indicateur, data={"yolo": "yolo"}
            )

    call_command("sync_metabase")

    assert MetabaseVSME.objects.count() == 3

    metabase_vsme_vide = MetabaseVSME.objects.get(
        entreprise__siren=entreprise_avec_vsme_vide.siren
    )
    assert metabase_vsme_vide.cree_le
    assert metabase_vsme_vide.modifie_le
    assert metabase_vsme_vide.statut == MetabaseVSME.STATUT_EN_COURS
    assert metabase_vsme_vide.nb_indicateurs_completes == 0
    assert metabase_vsme_vide.progression == 0
    for code in EXIGENCES_DE_PUBLICATION:
        assert getattr(metabase_vsme_vide, f"progression_{code}") == 0

    metabase_vsme_commencee = MetabaseVSME.objects.get(
        entreprise__siren=entreprise_avec_vsme_commencee.siren
    )
    assert metabase_vsme_commencee.statut == MetabaseVSME.STATUT_EN_COURS
    assert metabase_vsme_commencee.nb_indicateurs_completes == 1
    assert 0 < metabase_vsme_commencee.progression < 100
    assert 0 < metabase_vsme_commencee.progression_B1 < 100
    for code in EXIGENCES_DE_PUBLICATION:
        if code != "B1":
            assert getattr(metabase_vsme_commencee, f"progression_{code}") == 0

    metabase_vsme_terminee = MetabaseVSME.objects.get(
        entreprise__siren=entreprise_avec_vsme_terminee.siren
    )
    assert metabase_vsme_terminee.statut == MetabaseVSME.STATUT_A_JOUR
    assert metabase_vsme_terminee.nb_indicateurs_completes > 1
    assert metabase_vsme_terminee.progression == 100
    for code, exigence in EXIGENCES_DE_PUBLICATION.items():
        if exigence.remplissable:
            assert getattr(metabase_vsme_terminee, f"progression_{code}") == 100
        else:
            assert getattr(metabase_vsme_terminee, f"progression_{code}") == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_reglementations_plusieurs_fois(alice, entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001", effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    call_command("sync_metabase")
    call_command("sync_metabase")

    assert MetabaseBDESE.objects.count() == 1
    assert MetabaseIndexEgaPro.objects.count() == 1
    assert MetabaseBGES.objects.count() == 1


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_ignore_les_entreprises_inscrites_non_qualifiees_dans_la_synchro_des_reglementations(
    alice, entreprise_non_qualifiee
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")

    call_command("sync_metabase")

    assert MetabaseBDESE.objects.count() == 0
    assert MetabaseIndexEgaPro.objects.count() == 0
    assert MetabaseBGES.objects.count() == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_conserve_les_entreprises_inscrites_suffisamment_qualifiées_dans_la_synchro_des_reglementations(
    alice,
    entreprise_factory,
):
    # Ce cas arrive lorsqu'on ajoute une nouvelle caracteristique qualifiante dans les caracteristiques annuelles
    # Les anciennes caracteristiques ne sont plus qualifiantes mais peuvent être encore suffisamment qualifiantes pour des réglementations
    # Dans ce cas on veut les garder dans Metabase
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    caracteristiques.tranche_chiffre_affaires = None  # CA non renseigné
    caracteristiques.save()

    call_command("sync_metabase")

    # CA non nécessaire pour qualifier la BDESE
    assert MetabaseBDESE.objects.count() == 1
    # CA non nécessaire pour qualifier Index Egapro
    assert MetabaseIndexEgaPro.objects.count() == 1
    # CA non nécessaire pour qualifier BGES
    assert MetabaseBGES.objects.count() == 1


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_ignore_les_entreprises_inscrites_qui_ne_sont_pas_suffisamment_qualifiées_dans_la_synchro_des_reglementations(
    alice,
    entreprise_factory,
):
    # Si l'entreprise est insuffisamment qualifiée pour une réglementation
    # on ne met pas la réglementation de cette entreprise dans Metabase
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    caracteristiques.effectif = None  # effectif non renseigné
    caracteristiques.save()

    call_command("sync_metabase")

    # effectif nécessaire pour qualifier la BDESE
    assert MetabaseBDESE.objects.count() == 0
    # effectif nécessaire pour qualifier Index Egapro
    assert MetabaseIndexEgaPro.objects.count() == 0
    # effectif nécessaire pour qualifier Bilan GES
    assert MetabaseBGES.objects.count() == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_l_indicateur_d_impact_nombre_de_reglementations_a_jour(
    alice, bob, entreprise_factory, bdese_factory, mock_api_egapro, mock_api_bges
):
    entreprise_non_soumise = entreprise_factory(
        siren="000000001", effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    entreprise_tout_a_actualiser = entreprise_factory(
        siren="000000002", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    entreprise_tout_a_jour = entreprise_factory(
        siren="000000003", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    entreprise_bdese_a_jour = entreprise_factory(
        siren="000000004", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    for entreprise in (
        entreprise_non_soumise,
        entreprise_tout_a_actualiser,
        entreprise_tout_a_jour,
        entreprise_bdese_a_jour,
    ):
        Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    date_premiere_synchro = date(2020, 11, 28)
    with freeze_time(date_premiere_synchro):
        # une entreprise à jour pour Index Egapro sur 3 soumises
        mock_api_egapro.side_effect = [False, True, False]
        # deux entreprises à jour pour la BDESE sur 3 soumises
        bdese_a_actualiser = bdese_factory(
            bdese_class=BDESE_50_300,
            entreprise=entreprise_tout_a_actualiser,
            annee=derniere_annee_a_remplir_bdese(),
        )
        bdese_a_jour = bdese_factory(
            bdese_class=BDESE_50_300,
            entreprise=entreprise_tout_a_jour,
            annee=derniere_annee_a_remplir_bdese(),
        )
        bdese_a_jour_2 = bdese_factory(
            bdese_class=BDESE_50_300,
            entreprise=entreprise_bdese_a_jour,
            annee=derniere_annee_a_remplir_bdese(),
        )
        mark_bdese_as_complete(bdese_a_jour)
        mark_bdese_as_complete(bdese_a_jour_2)
        # aucune entreprise soumise au BGES

        call_command("sync_metabase")

    assert MetabaseStats.objects.count() == 1
    stat = MetabaseStats.objects.first()
    assert stat.date == date_premiere_synchro
    assert stat.reglementations_a_jour == 3  # 1 Index Egapro et 2 BDESE
    assert (
        stat.reglementations_statut_connu == 6
    )  # 3 entreprises soumises à la BDESE et Index Egapro dont on connait le statut


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_l_indicateur_d_impact_avec_des_entreprises_soumises_au_BGES(
    alice, bob, entreprise_factory, bdese_factory, mock_api_egapro, mock_api_bges
):
    entreprise_non_soumise = entreprise_factory(
        siren="000000001", effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    entreprise_bges_a_actualiser = entreprise_factory(
        siren="000000002", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
    )
    entreprise_bges_a_jour = entreprise_factory(
        siren="000000003", effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
    )
    for entreprise in (
        entreprise_non_soumise,
        entreprise_bges_a_actualiser,
        entreprise_bges_a_jour,
    ):
        Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    date_premiere_synchro = date(2020, 11, 28)
    with freeze_time(date_premiere_synchro):
        # aucune entreprise à jour pour Index Egapro sur 2 soumises
        mock_api_egapro.side_effect = [False, False]
        # aucune entreprise à jour pour BDESE sur 2 soumises
        # une entreprise à jour pour BGES sur 2 soumises
        # la première a un dépôt trop ancien, la deuxième suffisamment récent
        mock_api_bges.side_effect = [2010, 2023]

        call_command("sync_metabase")

    assert MetabaseStats.objects.count() == 1
    stat = MetabaseStats.objects.first()
    assert stat.date == date_premiere_synchro
    assert stat.reglementations_a_jour == 1  # 1 BGES
    assert (
        stat.reglementations_statut_connu == 6
    )  # 2 entreprises soumises à la BDESE, Index Egapro et BGES dont on connait le statut


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_les_stats_plusieurs_fois():
    date_premiere_synchro = date(2020, 11, 28)
    date_troisieme_synchro = date(2020, 11, 29)

    with freeze_time(date_premiere_synchro):
        call_command("sync_metabase")
        call_command("sync_metabase")

    assert MetabaseStats.objects.count() == 1
    stat = MetabaseStats.objects.first()
    assert stat.date == date_premiere_synchro

    with freeze_time(date_troisieme_synchro):
        call_command("sync_metabase")

    assert MetabaseStats.objects.count() == 2
    assert MetabaseStats.objects.get(date=date_premiere_synchro)
    assert MetabaseStats.objects.get(date=date_troisieme_synchro)
