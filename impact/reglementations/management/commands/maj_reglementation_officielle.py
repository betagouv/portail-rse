from django.core.management.base import BaseCommand

from reglementations.models.bdse import BDESE_300
from reglementations.models.bdse import BDESE_50_300
from reglementations.models.bdse import BDESEAvecAccord
from reglementations.models.csrd import RapportCSRD


class Command(BaseCommand):
    help = "Modifie le statut d'une règlementation (personnel / officiel)"

    # Permet de passer un rapport personnel en rapport officiel
    # en cas d'erreur du script de fusion.
    # Réglementations prises en compte :
    # - BDESE
    # - CSRD

    def add_arguments(self, parser):
        # les deux arguments suivants sont optionnels
        parser.add_argument(
            "--bdese", type=int, help="Identifiant de la BDESE (avec accord) à modifier"
        )
        parser.add_argument(
            "--bdese300", type=int, help="Identifiant de la BDESE 300 à modifier"
        )
        parser.add_argument(
            "--bdese50300", type=int, help="Identifiant de la BDESE 50_300 à modifier"
        )
        parser.add_argument(
            "--csrd", type=int, help="Identifiant du rapport CSRD à modifier"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Exécute la commande sans appliquer les modifications",
        )

    def handle(self, *args, **options):
        # Logique de la commande
        bdese = options["bdese"]
        bdese300 = options["bdese300"]
        bdese50300 = options["bdese50300"]
        csrd = options["csrd"]
        dry_run = options["dry_run"]

        clazz = None
        champ_utilisateur = "user"
        pk = None

        if bdese:
            clazz = BDESEAvecAccord
            pk = bdese
        elif bdese300:
            clazz = BDESE_300
            pk = bdese300
        elif bdese50300:
            clazz = BDESE_50_300
            pk = bdese50300
        elif csrd:
            clazz = RapportCSRD
            champ_utilisateur = "proprietaire"
            pk = csrd
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Un identifiant de BDESE ou de rapport CSRD doit être fourni"
                )
            )
            return

        query_params = {f"{champ_utilisateur}__isnull": False, "pk": pk}

        try:
            personnel = clazz.objects.get(**query_params)
        except clazz.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"L'élément {clazz.__name__}.{pk} n'existe pas ou n'est pas un rapport personnel"
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"> Le rapport personnel est : {clazz.__name__}.{personnel.pk} ({personnel})"
            )
        )

        try:
            query_params = {
                f"{champ_utilisateur}__isnull": True,
                "annee": personnel.annee,
                "entreprise_id": personnel.entreprise_id,
            }
            officiel = clazz.objects.get(**query_params)
        except clazz.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Il n'existe pas de rapport officiel à remplacer")
            )
            return

        # echange les deux rapports
        self.stdout.write(
            self.style.NOTICE(
                f"> L'ancien rapport officiel est : {clazz.__name__}.{officiel.pk} ({officiel})"
            )
        )

        if not dry_run:
            officiel.proprietaire = personnel.proprietaire
            personnel.proprietaire = None

            officiel.save()
            personnel.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Le rapport "{clazz.__name__}.{pk}" est maintenant officiel.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Le rapport "{clazz.__name__}.{pk}" serait maintenant officiel (dry-run).'
                )
            )
