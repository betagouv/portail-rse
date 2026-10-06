from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    help = "Supprime les utilisateurs de plus de 2 mois qui n'ont toujours pas confirmé leur email"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="log seulement les utilisateurs sans les supprimer réellement",
        )

    def handle(self, *args, **options):
        self.supprime_utilisateurs_non_confirmes(options)
        self.anonymise_utilisateurs_non_revenus(options)

    def supprime_utilisateurs_non_confirmes(self, options):
        il_y_a_deux_mois = date.today() + relativedelta(months=-2)

        if utilisateurs_a_supprimer := User.objects.filter(
            is_email_confirmed=False, created_at__date__lt=il_y_a_deux_mois
        ):
            self.stdout.write(
                "%s utilisateurs à supprimer" % len(utilisateurs_a_supprimer)
            )
            for utilisateur in utilisateurs_a_supprimer:
                if options["check"]:
                    self.stdout.write("Utilisateur à supprimer %s" % utilisateur.email)
                else:
                    utilisateur.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Utilisateur supprimé %s" % utilisateur.email
                        )
                    )
        else:
            self.stdout.write("Aucun utilisateur à supprimer")

    def anonymise_utilisateurs_non_revenus(self, options):
        il_y_a_trois_ans = date.today() + relativedelta(years=-3)

        if utilisateurs_a_anonymiser := User.objects.filter(
            last_login__date__lt=il_y_a_trois_ans
        ):
            self.stdout.write(
                "%s utilisateurs à anonymiser" % len(utilisateurs_a_anonymiser)
            )
            for utilisateur in utilisateurs_a_anonymiser:
                utilisateur.email = f"{utilisateur.id}@anonyme.invalid"
                utilisateur.prenom = "Personne"
                utilisateur.nom = "anonymisée"
                utilisateur.is_active = False
                utilisateur.save()
        else:
            self.stdout.write("Aucun utilisateur à anonymiser")
