from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from entreprises.models import Entreprise
from authentication.models import Utilisateur


EMAIL_J7 = {
    'sujet': 'Votre abonnement FinanceIQ expire dans 7 jours',
    'corps': (
        "Bonjour {nom_entreprise},\n\n"
        "Nous espérons que FinanceIQ vous aide à gérer votre activité au quotidien.\n\n"
        "Nous vous informons que votre abonnement arrive à échéance le {date_echeance}.\n"
        "Pour assurer la continuité de votre accès sans interruption, nous vous invitons "
        "à nous contacter dès maintenant.\n\n"
        "📧 {email_contact}\n\n"
        "Merci pour votre confiance,\n"
        "L'équipe FinanceIQ"
    ),
}

EMAIL_J3 = {
    'sujet': '⚠️ Votre accès FinanceIQ sera suspendu dans 3 jours',
    'corps': (
        "Bonjour {nom_entreprise},\n\n"
        "Ceci est un rappel urgent : votre accès à FinanceIQ sera automatiquement "
        "suspendu le {date_blocage} si votre abonnement n'est pas renouvelé.\n\n"
        "Pour éviter toute interruption de service et la perte d'accès à vos données "
        "financières, contactez-nous sans attendre :\n\n"
        "📧 {email_contact}\n\n"
        "Si vous avez déjà effectué votre paiement, ignorez ce message — "
        "votre accès sera maintenu.\n\n"
        "Cordialement,\n"
        "L'équipe FinanceIQ"
    ),
}


class Command(BaseCommand):
    help = 'Envoie les rappels d\'abonnement J-7 et J-3 aux clients'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Simule sans envoyer d\'emails')

    def handle(self, *args, **options):
        dry_run      = options['dry_run']
        today        = timezone.now().date()
        grace        = timedelta(days=Entreprise.GRACE_DAYS)
        email_contact = settings.DEFAULT_FROM_EMAIL
        envoyes      = 0
        ignores      = 0

        entreprises = Entreprise.objects.exclude(plan='suspendu').filter(
            utilisateurs__role='admin'
        ).distinct()

        for entreprise in entreprises:
            # Déterminer la date d'échéance selon le plan
            if entreprise.plan == 'essai':
                date_fin = entreprise.date_fin_essai
            elif entreprise.plan == 'payant':
                date_fin = entreprise.date_fin_abonnement
            else:
                continue

            if not date_fin:
                continue

            date_blocage = date_fin + grace
            jours_restants = (date_blocage - today).days

            # Choisir le bon email selon le nombre de jours restants
            if jours_restants == 7:
                template = EMAIL_J7
            elif jours_restants == 3:
                template = EMAIL_J3
            else:
                ignores += 1
                continue

            # Récupérer l'email de l'admin de l'entreprise
            admin = Utilisateur.objects.filter(
                id_entreprise=entreprise, role='admin'
            ).first()

            if not admin or not admin.email:
                self.stdout.write(self.style.WARNING(
                    f'  [SKIP] {entreprise.nom} — pas d\'email admin'
                ))
                ignores += 1
                continue

            sujet = template['sujet']
            corps = template['corps'].format(
                nom_entreprise=entreprise.nom,
                date_echeance=date_fin.strftime('%d/%m/%Y'),
                date_blocage=date_blocage.strftime('%d/%m/%Y'),
                email_contact=email_contact,
            )

            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] {entreprise.nom} → {admin.email} '
                    f'(J-{jours_restants}) : {sujet}'
                )
            else:
                try:
                    send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL,
                              [admin.email], fail_silently=False)
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ {entreprise.nom} → {admin.email} (J-{jours_restants})'
                    ))
                    envoyes += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ {entreprise.nom} — erreur: {e}'
                    ))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Aucun email envoyé.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\n{envoyes} email(s) envoyé(s), {ignores} ignoré(s).'
            ))
