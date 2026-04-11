from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction
from budgets.models import Budget
from .models import Alerte
from django.db.models import Sum


def get_creances_info(entreprise):
    """Récupère les informations sur les créances clients"""
    from dettes_factures.models import DetteFacture
    creances = DetteFacture.objects.filter(
        id_entreprise=entreprise,
        type='Client',
        statut__in=['en_cours', 'partiellement_paye']
    )
    total = sum(
        float(c.montant_total) - float(c.montant_paye)
        for c in creances
    )
    return len(creances), total


@receiver(post_save, sender=Transaction)
def verifier_tresorerie(sender, instance, created, **kwargs):
    if not created:
        return

    entreprise = instance.id_entreprise

    entrees = Transaction.objects.filter(
        id_entreprise=entreprise,
        type='Entree'
    ).aggregate(total=Sum('montant'))['total'] or 0

    sorties = Transaction.objects.filter(
        id_entreprise=entreprise,
        type='Sortie'
    ).aggregate(total=Sum('montant'))['total'] or 0

    solde = float(entrees) - float(sorties)

    nb_creances, total_creances = get_creances_info(entreprise)

    # Alerte trésorerie négative
    if solde < 0:
        recommandations = f"""
⚠️ TRÉSORERIE NÉGATIVE — Solde : {solde:,.0f} XOF

📊 SITUATION :
- Total entrées : {float(entrees):,.0f} XOF
- Total sorties : {float(sorties):,.0f} XOF
- Déficit : {abs(solde):,.0f} XOF

💡 RECOMMANDATIONS :
1. 📞 Relancez vos {nb_creances} créanciers — ils vous doivent {total_creances:,.0f} XOF
2. 🚫 Suspendez toute dépense non essentielle immédiatement
3. 💰 Cherchez un financement d'urgence ou un découvert bancaire
4. 📋 Générez un rapport mensuel pour analyser les flux
5. 🔄 Négociez des délais de paiement avec vos fournisseurs
        """.strip()

        Alerte.objects.create(
            message=recommandations,
            type_alerte='baisse_tresorerie',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )

    # Alerte trésorerie faible
    elif solde < 500000:
        recommandations = f"""
📉 TRÉSORERIE FAIBLE — Solde : {solde:,.0f} XOF

📊 SITUATION :
- Solde actuel : {solde:,.0f} XOF
- Seuil critique : 500 000 XOF

💡 RECOMMANDATIONS :
1. 📞 Relancez vos créanciers — montant à recevoir : {total_creances:,.0f} XOF
2. 📉 Limitez les dépenses au strict nécessaire
3. 📊 Analysez vos postes de dépenses les plus importants
4. 💼 Accélérez vos actions commerciales pour générer des entrées
        """.strip()

        Alerte.objects.create(
            message=recommandations,
            type_alerte='baisse_tresorerie',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )


@receiver(post_save, sender=Transaction)
def verifier_budget(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.type != 'Sortie':
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

    total_sorties = Transaction.objects.filter(
        id_entreprise=entreprise,
        id_categorie=id_categorie,
        type='Sortie',
        date_transaction__gte=budget.date_debut,
        date_transaction__lte=budget.date_fin,
    ).aggregate(total=Sum('montant'))['total'] or 0

    budget.montant_consomme = total_sorties
    budget.save()

    taux = (float(total_sorties) / float(budget.montant_limite)) * 100
    depassement = float(total_sorties) - float(budget.montant_limite)

    # Alerte budget dépassé
    if total_sorties > budget.montant_limite:
        recommandations = f"""
🚨 BUDGET DÉPASSÉ — Catégorie : {id_categorie}

📊 SITUATION :
- Montant consommé : {float(total_sorties):,.0f} XOF
- Limite fixée : {float(budget.montant_limite):,.0f} XOF
- Dépassement : {depassement:,.0f} XOF ({taux:.0f}%)

💡 RECOMMANDATIONS :
1. 🚫 Suspendez immédiatement les dépenses dans cette catégorie
2. 📋 Révisez le budget pour la prochaine période
3. 🔍 Analysez les causes du dépassement
4. 💼 Compensez avec une réduction dans d'autres catégories
        """.strip()

        Alerte.objects.create(
            message=recommandations,
            type_alerte='depassement_budget',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )

    # Alerte budget à 75%
    elif total_sorties >= float(budget.montant_limite) * 0.75:
        recommandations = f"""
⚠️ BUDGET À {taux:.0f}% — Catégorie : {id_categorie}

📊 SITUATION :
- Consommé : {float(total_sorties):,.0f} XOF
- Limite : {float(budget.montant_limite):,.0f} XOF
- Reste : {float(budget.montant_limite) - float(total_sorties):,.0f} XOF

💡 RECOMMANDATIONS :
1. ⚠️ Ralentissez les dépenses dans cette catégorie
2. 📊 Vérifiez si le budget est suffisant pour la période
3. 🔄 Envisagez de réajuster le budget si nécessaire
        """.strip()

        Alerte.objects.create(
            message=recommandations,
            type_alerte='depassement_budget',
            id_entreprise=entreprise,
            id_utilisateur=instance.id_utilisateur,
        )
