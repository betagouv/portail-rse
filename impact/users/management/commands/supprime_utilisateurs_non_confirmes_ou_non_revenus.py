from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User
from users.models import anonymise_un_utilisateur


class Command(BaseCommand):
    help = "Supprime les utilisateurs de plus de 2 mois qui n'ont toujours pas confirmé leur email, alerte ou anonymise les utilisateurs qui ne sont pas reconnectés depuis plus de 3 ans"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="log seulement les utilisateurs sans les supprimer, alerter ou anonymiser réellement",
        )

    def handle(self, *args, **options):
        self.supprime_utilisateurs_non_confirmes(options)
        self.alerte_utilisateurs_non_revenus(options)
        self.anonymise_utilisateurs_non_revenus_apres_alerte(options)

    def supprime_utilisateurs_non_confirmes(self, options):
        il_y_a_deux_mois = date.today() + relativedelta(months=-2)

        if utilisateurs_a_supprimer := User.objects.filter(
            is_email_confirmed=False, created_at__date__lt=il_y_a_deux_mois
        ):
            self.stdout.write(
                f"{len(utilisateurs_a_supprimer)} utilisateurs à supprimer"
            )
            for utilisateur in utilisateurs_a_supprimer:
                message = f"Utilisateur à supprimer {utilisateur.email}"
                if options["check"]:
                    self.stdout.write(message)
                else:
                    utilisateur.delete()
                    self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write("Aucun utilisateur à supprimer")

    def alerte_utilisateurs_non_revenus(self, options):
        il_y_a_deux_ans_et_onze_mois = date.today() + relativedelta(
            years=-2, months=-11
        )

        if utilisateurs_a_alerter := User.objects.filter(
            last_login__date__lt=il_y_a_deux_ans_et_onze_mois,
            date_alerte_anonymisation__isnull=True,
            is_active=True,
        ):
            self.stdout.write(
                f"{len(utilisateurs_a_alerter)} utilisateurs à alerter avant anonymisation"
            )
            for utilisateur in utilisateurs_a_alerter:
                message = f"Utilisateur à alerter {utilisateur.email}"
                if options["check"]:
                    self.stdout.write(message)
                else:
                    try:
                        _envoie_email_pour_risque_d_anonymisation(utilisateur)
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(
                                f"Échec de l'alerte de {utilisateur.email} : {e}"
                            )
                        )
                        continue
                    utilisateur.date_alerte_anonymisation = timezone.now()
                    utilisateur.save()
                    self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write("Aucun utilisateur à alerter avant anonymisation")

    def anonymise_utilisateurs_non_revenus_apres_alerte(self, options):
        il_y_a_trente_jours = timezone.now() + relativedelta(days=-30)

        if utilisateurs_a_anonymiser := User.objects.filter(
            date_alerte_anonymisation__date__lt=il_y_a_trente_jours,
            is_active=True,
        ):
            self.stdout.write(
                f"{len(utilisateurs_a_anonymiser)} utilisateurs à anonymiser"
            )
            for utilisateur in utilisateurs_a_anonymiser:
                message = f"Utilisateur à anonymiser {utilisateur.email}"
                if options["check"]:
                    self.stdout.write(message)
                else:
                    anonymise_un_utilisateur(utilisateur)
                    self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write("Aucun utilisateur à anonymiser")


def _envoie_email_pour_risque_d_anonymisation(utilisateur):
    email = EmailMessage(
        to=[utilisateur.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_ANONYMISATION_FUTURE_TEMPLATE
    email.send()
