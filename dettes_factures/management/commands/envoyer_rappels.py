"""
Commande : python manage.py envoyer_rappels

Envoie automatiquement des emails de rappel pour :
  - Les dettes clients en retard (date_echeance dépassée)
  - Les dettes clients à échéance dans 3 jours ou moins

À programmer dans le Planificateur de tâches Windows pour s'exécuter chaque matin.
"""
import datetime
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from dettes_factures.models import DetteFacture


class Command(BaseCommand):
    help = 'Envoie les rappels automatiques pour les dettes arrivant à échéance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jours',
            type=int,
            default=3,
            help='Nombre de jours avant échéance pour déclencher le rappel (défaut: 3)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait envoyé sans envoyer les emails',
        )

    def handle(self, *args, **options):
        today     = datetime.date.today()
        j_limite  = today + datetime.timedelta(days=options['jours'])
        dry_run   = options['dry_run']
        envoyes   = 0
        ignores   = 0

        # Dettes clients non soldées : en retard OU à échéance prochaine
        dettes = DetteFacture.objects.select_related(
            'id_tiers', 'id_entreprise',
            'id_entreprise__utilisateurs'
        ).filter(
            type='Client',
            statut__in=['en_cours', 'partiellement_paye', 'en_retard'],
            date_echeance__lte=j_limite,
        )

        self.stdout.write(f"[{today}] {dettes.count()} dette(s) à traiter...")

        for dette in dettes:
            tiers      = dette.id_tiers
            entreprise = dette.id_entreprise
            restant    = float(dette.montant_total) - float(dette.montant_paye or 0)
            echeance   = dette.date_echeance.strftime('%d/%m/%Y')
            en_retard  = dette.date_echeance < today

            # Récupérer l'email du propriétaire (admin) de l'entreprise
            admin = entreprise.utilisateurs.filter(role='admin').first()
            email_admin = admin.email if admin and admin.email else None

            destinataires = []
            if tiers.email:
                destinataires.append(tiers.email)
            if email_admin:
                destinataires.append(email_admin)

            if not destinataires:
                self.stdout.write(f"  ⚠ {tiers.nom} — aucun email disponible, ignoré.")
                ignores += 1
                continue

            statut_txt = "EN RETARD" if en_retard else f"dans {(dette.date_echeance - today).days} jour(s)"
            sujet = f"{'[RETARD] ' if en_retard else ''}Rappel de paiement — {entreprise.nom}"
            corps = (
                f"Bonjour {tiers.nom},\n\n"
                f"{'⚠ Ce paiement est EN RETARD.' if en_retard else 'Votre paiement arrive bientôt à échéance.'}\n\n"
                f"Détails :\n"
                f"— Entreprise       : {entreprise.nom}\n"
                f"— Montant restant  : {restant:,.0f} XOF\n"
                f"— Date d'échéance  : {echeance} ({statut_txt})\n\n"
                f"Merci de procéder au règlement dans les meilleurs délais.\n\n"
                f"Cordialement,\n{entreprise.nom}\n\n"
                f"— Email généré automatiquement par FinanceIQ —"
            )

            if dry_run:
                self.stdout.write(
                    f"  [DRY-RUN] {tiers.nom} ({statut_txt}) → {', '.join(destinataires)}"
                )
            else:
                try:
                    send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, destinataires, fail_silently=False)
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Rappel envoyé : {tiers.nom} ({statut_txt}) → {', '.join(destinataires)}"
                    ))
                    envoyes += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Erreur ({tiers.nom}) : {e}"))
                    ignores += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\n[DRY-RUN] {dettes.count()} dette(s) analysées — aucun email envoyé."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nTerminé : {envoyes} email(s) envoyé(s), {ignores} ignoré(s)."))
