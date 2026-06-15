from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from transactions.models import Transaction
from budgets.models import Budget
from .models import Alerte
from django.db.models import Sum
import datetime


def envoyer_alerte_email(utilisateur, sujet, message):
    if not utilisateur.email:
        return
    try:
        send_mail(
            subject=f'[FinanceIQ] {sujet}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=True,
        )
    except Exception:
        pass


def alerte_recente_existe(entreprise, type_alerte, heures=24, mot_cle=None):
    """
    Retourne True si une alerte similaire a déjà été émise
    dans la fenêtre de temps donnée, pour éviter les doublons.
    mot_cle permet de distinguer les sous-types (ex: 'NÉGATIVE' vs 'FAIBLE',
    ou le nom d'une catégorie budgétaire).
    """
    depuis = timezone.now() - datetime.timedelta(hours=heures)
    qs = Alerte.objects.filter(
        id_entreprise=entreprise,
        type_alerte=type_alerte,
        date_emission__gte=depuis,
    )
    if mot_cle:
        qs = qs.filter(message__icontains=mot_cle)
    return qs.exists()


def get_creances_info(entreprise):
    """
    Retourne les créances clients non soldées (y compris partiellement payées),
    triées du plus en retard au plus récent.
    Limite à 3 clients en temps normal, 4 si au moins 3 sont déjà en retard.
    """
    from dettes_factures.models import DetteFacture
    aujourd_hui = datetime.date.today()

    creances = DetteFacture.objects.select_related('id_tiers', 'id_transaction').filter(
        id_entreprise=entreprise,
        type='Client',
        statut__in=['en_cours', 'partiellement_paye', 'en_retard']
    ).order_by('date_echeance')  # plus ancienne échéance = plus urgent = en premier

    total = sum(float(c.montant_total) - float(c.montant_paye) for c in creances)
    nb_total = len(creances)

    # Détermine combien afficher : 4 si ≥3 sont en retard, sinon 3
    nb_en_retard = sum(1 for c in creances if (aujourd_hui - c.date_echeance).days > 0)
    nb_a_afficher = 4 if nb_en_retard >= 3 else 3

    lignes = []
    for c in creances[:nb_a_afficher]:
        montant_total = float(c.montant_total)
        montant_paye  = float(c.montant_paye)
        restant       = montant_total - montant_paye
        ecart_jours   = (aujourd_hui - c.date_echeance).days
        nom           = c.id_tiers.nom if c.id_tiers else 'Client inconnu'

        # Date à laquelle le client a pris le produit/service
        if c.id_transaction and c.id_transaction.date_transaction:
            date_achat = c.id_transaction.date_transaction.strftime('%d/%m/%Y')
            jours_depuis = (aujourd_hui - c.id_transaction.date_transaction).days
        else:
            date_achat    = '(non renseignée)'
            jours_depuis  = None

        # Infos de contact
        contact_parts = []
        if c.id_tiers and c.id_tiers.telephone:
            contact_parts.append(f'Tél : {c.id_tiers.telephone}')
        if c.id_tiers and c.id_tiers.email:
            contact_parts.append(f'Email : {c.id_tiers.email}')
        contact = '  |  '.join(contact_parts)

        # Libellé d'urgence selon le retard
        if ecart_jours > 0:
            urgence = f'EN RETARD de {ecart_jours} jour{"s" if ecart_jours > 1 else ""}  ⛔'
        elif ecart_jours == 0:
            urgence = "Échéance AUJOURD'HUI  🔴"
        elif ecart_jours >= -7:
            urgence = f'Échéance dans {-ecart_jours} jour{"s" if -ecart_jours > 1 else ""}  🟠'
        else:
            urgence = f'Échéance le {c.date_echeance.strftime("%d/%m/%Y")}  🟡'

        # Mention paiement partiel
        paiement_partiel = montant_paye > 0

        lignes.append({
            'nom':              nom,
            'montant_total':    montant_total,
            'montant_paye':     montant_paye,
            'restant':          restant,
            'paiement_partiel': paiement_partiel,
            'date_achat':       date_achat,
            'jours_depuis':     jours_depuis,
            'echeance':         c.date_echeance,
            'urgence':          urgence,
            'contact':          contact,
            'ecart_jours':      ecart_jours,
        })

    return nb_total, total, lignes, nb_en_retard


def formater_liste_creances(lignes, nb_total):
    """Formate la liste clients prioritaires pour l'affichage dans une alerte."""
    if not lignes:
        return '  Aucune créance client enregistrée.'

    texte = ''
    for i, c in enumerate(lignes, 1):
        texte += f'\n  {i}. {c["nom"]}\n'

        # Détail financier
        if c['paiement_partiel']:
            texte += f'     Montant initial  : {c["montant_total"]:,.0f} XOF\n'
            texte += f'     Déjà payé        : {c["montant_paye"]:,.0f} XOF  ✓ (paiement partiel)\n'
            texte += f'     Reste à réclamer : {c["restant"]:,.0f} XOF  ← À recouvrer\n'
        else:
            texte += f'     Montant à recouvrer : {c["restant"]:,.0f} XOF\n'

        # Date d'achat et ancienneté
        if c['jours_depuis'] is not None:
            texte += f'     Produit/service pris le : {c["date_achat"]} (il y a {c["jours_depuis"]} jours)\n'
        else:
            texte += f'     Produit/service pris le : {c["date_achat"]}\n'

        texte += f'     Échéance prévue  : {c["echeance"].strftime("%d/%m/%Y")}\n'
        texte += f'     Statut           : {c["urgence"]}\n'

        if c['contact']:
            texte += f'     Contact          : {c["contact"]}\n'

    # Si d'autres clients non affichés
    nb_affiches = len(lignes)
    if nb_total > nb_affiches:
        texte += f'\n  + {nb_total - nb_affiches} autre{"s" if nb_total - nb_affiches > 1 else ""} client{"s" if nb_total - nb_affiches > 1 else ""} à relancer (voir page Dettes & Factures)\n'

    return texte.rstrip()


def get_dettes_urgentes(entreprise):
    from dettes_factures.models import DetteFacture
    aujourd_hui = datetime.date.today()
    dettes = DetteFacture.objects.filter(
        id_entreprise=entreprise,
        type='Fournisseur',
        statut__in=['en_cours', 'partiellement_paye', 'en_retard'],
        date_echeance__lte=aujourd_hui + datetime.timedelta(days=30)
    ).order_by('date_echeance')
    total = sum(float(d.montant_total) - float(d.montant_paye) for d in dettes)
    return len(dettes), total


def calcul_vitesse_depenses(entreprise, jours=30):
    depuis = datetime.date.today() - datetime.timedelta(days=jours)
    total  = Transaction.objects.filter(
        id_entreprise=entreprise,
        type='Sortie',
        date_transaction__gte=depuis,
    ).aggregate(total=Sum('montant'))['total'] or 0
    return float(total) / jours if jours > 0 else 0


def get_nom_categorie(id_categorie):
    try:
        from categories.models import Categorie
        return Categorie.objects.get(id=id_categorie).nom_categorie
    except Exception:
        return f'Catégorie #{id_categorie}'


@receiver(post_save, sender=Transaction)
def verifier_tresorerie(sender, instance, created, **kwargs):
    if not created:
        return

    entreprise  = instance.id_entreprise
    aujourd_hui = datetime.date.today()

    entrees = float(Transaction.objects.filter(
        id_entreprise=entreprise, type='Entree'
    ).aggregate(total=Sum('montant'))['total'] or 0)

    sorties = float(Transaction.objects.filter(
        id_entreprise=entreprise, type='Sortie'
    ).aggregate(total=Sum('montant'))['total'] or 0)

    solde = entrees - sorties

    nb_creances, total_creances, lignes_creances, nb_en_retard = get_creances_info(entreprise)
    nb_dettes, total_dettes                                    = get_dettes_urgentes(entreprise)
    vitesse_quotidienne                                        = calcul_vitesse_depenses(entreprise, jours=30)
    jours_survie  = int(solde / vitesse_quotidienne) if vitesse_quotidienne > 0 and solde > 0 else 0
    liste_clients = formater_liste_creances(lignes_creances, nb_creances)

    # ──────────────────────────────────────────
    # TRÉSORERIE NÉGATIVE
    # ──────────────────────────────────────────
    if solde < 0:
        # Pas de doublon : 1 alerte "NÉGATIVE" max toutes les 24h
        if alerte_recente_existe(entreprise, 'baisse_tresorerie', heures=24, mot_cle='NÉGATIVE'):
            return

        deficit          = abs(solde)
        ratio_couverture = (entrees / sorties * 100) if sorties > 0 else 0

        message = f"""ALERTE CRITIQUE — TRÉSORERIE NÉGATIVE
Détectée le {aujourd_hui.strftime('%d/%m/%Y')} à {timezone.now().strftime('%H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAT DE LA TRÉSORERIE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Solde actuel       :  {solde:>14,.0f} XOF  ⛔
  Total des entrées  :  {entrees:>14,.0f} XOF
  Total des sorties  :  {sorties:>14,.0f} XOF
  Déficit            :  {deficit:>14,.0f} XOF
  Taux de couverture :  {ratio_couverture:>13.1f} %

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLIENTS À RELANCER EN PRIORITÉ — {nb_creances} client{"s" if nb_creances > 1 else ""}
Total récupérable : {total_creances:,.0f} XOF
(Du plus en retard au moins en retard)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{liste_clients}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTRES LEVIERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Dettes fournisseurs à 30 j :  {total_dettes:>10,.0f} XOF  ({nb_dettes} échéance{"s" if nb_dettes > 1 else ""})
  Solde potentiel             :  {solde + total_creances:>10,.0f} XOF  (si toutes créances recouvrées)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIONS PRIORITAIRES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URGENT — Dans les 24 heures :
  1. Appelez chaque client listé ci-dessus, en commençant par le n°1
  2. Bloquez toutes les dépenses non contractuelles immédiatement
  3. Informez votre comptable ou conseiller financier de la situation

COURT TERME — Cette semaine :
  4. Proposez un escompte de 3-5% aux clients pour tout paiement immédiat
  5. Négociez un découvert bancaire autorisé en urgence
  6. Demandez un report d'échéance à vos fournisseurs ({total_dettes:,.0f} XOF)

MOYEN TERME — Ce mois :
  7. Supprimez ou gelez les charges fixes non essentielles
  8. Mettez en place une prévision de trésorerie à 90 jours
  9. Envisagez l'affacturage pour accélérer l'encaissement de vos factures

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cette alerte a été générée automatiquement par FinanceIQ.
""".strip()

        Alerte.objects.create(
            message=message,
            type_alerte='baisse_tresorerie',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )
        envoyer_alerte_email(instance.id_utilisateur, 'URGENT — Trésorerie négative', message)

    # ──────────────────────────────────────────
    # TRÉSORERIE FAIBLE
    # ──────────────────────────────────────────
    elif solde < 500_000:
        # Pas de doublon : 1 alerte "FAIBLE" max toutes les 24h
        if alerte_recente_existe(entreprise, 'baisse_tresorerie', heures=24, mot_cle='FAIBLE'):
            return

        pct_couverture = (solde / 500_000) * 100

        message = f"""ALERTE — TRÉSORERIE FAIBLE
Détectée le {aujourd_hui.strftime('%d/%m/%Y')} à {timezone.now().strftime('%H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAT DE LA TRÉSORERIE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Solde actuel       :  {solde:>14,.0f} XOF  ⚠️
  Seuil de vigilance :      500 000 XOF
  Marge de sécurité  :  {pct_couverture:>13.1f} %
  Autonomie estimée  :  {jours_survie:>9} jour{"s" if jours_survie > 1 else ""}  (au rythme actuel)
  Dépense quotidienne:  {vitesse_quotidienne:>14,.0f} XOF/jour

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLIENTS À RELANCER — {nb_creances} client{"s" if nb_creances > 1 else ""}
Total récupérable : {total_creances:,.0f} XOF
(Du plus en retard au moins en retard)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{liste_clients}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTRES LEVIERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Dettes fournisseurs à 30 j :  {total_dettes:>10,.0f} XOF  ({nb_dettes} échéance{"s" if nb_dettes > 1 else ""})
  Solde si recouvrements      :  {solde + total_creances:>10,.0f} XOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIONS RECOMMANDÉES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMMÉDIAT :
  1. Appelez chaque client listé ci-dessus, en commençant par le n°1
  2. Reportez toute dépense non urgente à la semaine prochaine
  3. Vérifiez les échéances à venir pour anticiper les sorties

CETTE SEMAINE :
  4. Analysez vos 5 postes de dépenses les plus importants
  5. Accélérez votre cycle de facturation clients
  6. Prévoyez une réserve équivalente à 2 mois de charges fixes

CE MOIS :
  7. Fixez un solde minimum de trésorerie (recommandé : 2 mois de charges)
  8. Mettez en place une prévision de trésorerie à 90 jours
  9. Envisagez une ligne de crédit préventive auprès de votre banque

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cette alerte a été générée automatiquement par FinanceIQ.
""".strip()

        Alerte.objects.create(
            message=message,
            type_alerte='baisse_tresorerie',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )
        envoyer_alerte_email(instance.id_utilisateur, 'Vigilance — Trésorerie faible', message)


@receiver(post_save, sender=Transaction)
def verifier_budget(sender, instance, created, **kwargs):
    if not created or instance.type != 'Sortie':
        return

    entreprise   = instance.id_entreprise
    id_categorie = instance.id_categorie

    try:
        budget = Budget.objects.get(
            id_entreprise=entreprise,
            id_categorie=id_categorie,
            date_debut__lte=instance.date_transaction,
            date_fin__gte=instance.date_transaction,
        )
    except Budget.DoesNotExist:
        return

    total_sorties = float(Transaction.objects.filter(
        id_entreprise=entreprise,
        id_categorie=id_categorie,
        type='Sortie',
        date_transaction__gte=budget.date_debut,
        date_transaction__lte=budget.date_fin,
    ).aggregate(total=Sum('montant'))['total'] or 0)

    budget.montant_consomme = total_sorties
    budget.save()

    limite      = float(budget.montant_limite)
    taux        = (total_sorties / limite) * 100 if limite > 0 else 0
    reste       = limite - total_sorties
    depassement = total_sorties - limite
    nom_cat     = get_nom_categorie(id_categorie)
    aujourd_hui = datetime.date.today()

    jours_restants           = max((budget.date_fin - aujourd_hui).days, 0)
    jours_total              = max((budget.date_fin - budget.date_debut).days, 1)
    jours_ecoules            = max(jours_total - jours_restants, 1)
    budget_journalier_ideal  = limite / jours_total
    depense_journaliere_reel = total_sorties / jours_ecoules
    projection_fin           = depense_journaliere_reel * jours_total

    # ──────────────────────────────────────────
    # BUDGET DÉPASSÉ
    # ──────────────────────────────────────────
    if total_sorties > limite:
        # Pas de doublon : 1 alerte "DÉPASSÉ" par catégorie toutes les 48h
        if alerte_recente_existe(entreprise, 'depassement_budget', heures=48, mot_cle=f'BUDGET DÉPASSÉ\nCatégorie : {nom_cat}'):
            return
        message = f"""ALERTE CRITIQUE — BUDGET DÉPASSÉ
Catégorie : {nom_cat}
Détectée le {aujourd_hui.strftime('%d/%m/%Y')} à {timezone.now().strftime('%H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAT DU BUDGET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Budget alloué       :  {limite:>14,.0f} XOF
  Montant consommé    :  {total_sorties:>14,.0f} XOF  ⛔
  Dépassement         :  {depassement:>14,.0f} XOF  (+{taux - 100:.1f}%)
  Taux de consommation:  {taux:>13.1f} %
  Période             :  {budget.date_debut.strftime('%d/%m/%Y')} → {budget.date_fin.strftime('%d/%m/%Y')}
  Jours restants      :  {jours_restants} jour{"s" if jours_restants > 1 else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Dépense quotidienne réelle  :  {depense_journaliere_reel:>10,.0f} XOF/jour
  Budget quotidien prévu      :  {budget_journalier_ideal:>10,.0f} XOF/jour
  Écart quotidien             :  {depense_journaliere_reel - budget_journalier_ideal:>+10,.0f} XOF/jour
  Projection fin de période   :  {projection_fin:>10,.0f} XOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIONS PRIORITAIRES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMMÉDIAT :
  1. Gel immédiat de toutes les dépenses "{nom_cat}" jusqu'à fin de période
  2. Aucun bon de commande ni engagement sans validation préalable
  3. Informez votre responsable hiérarchique ou associé

COURT TERME :
  4. Identifiez les transactions ayant causé le dépassement
  5. Négociez un retour ou un avoir si des dépenses sont récentes
  6. Compensez en réduisant d'autres catégories à faible priorité

PROCHAINE PÉRIODE :
  7. Réévaluez le budget "{nom_cat}" à la hausse ({int(projection_fin * 1.1):,.0f} XOF recommandé)
  8. Mettez en place une validation obligatoire dès 80% du budget atteint
  9. Découpez ce poste en sous-catégories pour un meilleur suivi

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cette alerte a été générée automatiquement par FinanceIQ.
""".strip()

        Alerte.objects.create(
            message=message,
            type_alerte='depassement_budget',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )
        envoyer_alerte_email(instance.id_utilisateur, f'URGENT — Budget "{nom_cat}" dépassé à {taux:.0f}%', message)

    # ──────────────────────────────────────────
    # BUDGET À 75%+
    # ──────────────────────────────────────────
    elif total_sorties >= limite * 0.75:
        # Pas de doublon : 1 alerte "À X%" par catégorie toutes les 24h
        if alerte_recente_existe(entreprise, 'depassement_budget', heures=24, mot_cle=f'BUDGET À\nCatégorie : {nom_cat}'):
            return
        budget_restant_jours = reste / depense_journaliere_reel if depense_journaliere_reel > 0 else jours_restants
        risque_depassement   = projection_fin > limite

        message = f"""ALERTE — BUDGET À {taux:.0f}%
Catégorie : {nom_cat}
Détectée le {aujourd_hui.strftime('%d/%m/%Y')} à {timezone.now().strftime('%H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAT DU BUDGET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Budget alloué       :  {limite:>14,.0f} XOF
  Montant consommé    :  {total_sorties:>14,.0f} XOF  ⚠️
  Reste disponible    :  {reste:>14,.0f} XOF
  Taux de consommation:  {taux:>13.1f} %
  Période             :  {budget.date_debut.strftime('%d/%m/%Y')} → {budget.date_fin.strftime('%d/%m/%Y')}
  Jours restants      :  {jours_restants} jour{"s" if jours_restants > 1 else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE PRÉDICTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Dépense quotidienne actuelle  :  {depense_journaliere_reel:>8,.0f} XOF/jour
  Budget quotidien prévu        :  {budget_journalier_ideal:>8,.0f} XOF/jour
  Budget restant épuisé dans    :  {int(budget_restant_jours):>5} jour{"s" if int(budget_restant_jours) > 1 else ""}
  Projection fin de période     :  {projection_fin:>8,.0f} XOF
  {"⛔ RISQUE DE DÉPASSEMENT détecté" if risque_depassement else "✅ Dans les limites si le rythme est maintenu"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIONS RECOMMANDÉES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMMÉDIAT :
  1. Réduisez les dépenses "{nom_cat}" à max {reste / jours_restants if jours_restants > 0 else 0:,.0f} XOF/jour
  2. Passez en revue les engagements futurs dans cette catégorie
  3. Priorisez uniquement les dépenses indispensables

CETTE SEMAINE :
  4. Identifiez les dépenses encore évitables ou reportables
  5. Si une dépense importante est incontournable, réévaluez le budget maintenant
  6. Comparez votre consommation avec les périodes précédentes

CE MOIS :
  7. Analysez les causes de la montée rapide de ce poste
  8. Définissez un plafond d'alerte à 70% pour anticiper plus tôt
  9. Prochain budget conseillé : {int(projection_fin * 1.05):,.0f} XOF (+5% de marge)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cette alerte a été générée automatiquement par FinanceIQ.
""".strip()

        Alerte.objects.create(
            message=message,
            type_alerte='depassement_budget',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )
        envoyer_alerte_email(instance.id_utilisateur, f'Vigilance — Budget "{nom_cat}" à {taux:.0f}%', message)
