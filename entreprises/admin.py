from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Entreprise


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display    = ('nom', 'plan_badge', 'acces_badge', 'date_echeance', 'date_blocage_auto', 'devise', 'nb_utilisateurs', 'nb_transactions')
    search_fields   = ('nom',)
    list_filter     = ('plan', 'devise')
    ordering        = ('nom',)
    readonly_fields = ('logo_apercu', 'acces_badge')
    fields          = ('nom', 'logo', 'logo_apercu', 'devise', 'date_creation', 'plan', 'date_fin_essai', 'date_fin_abonnement')
    actions         = ['passer_en_payant_1mois', 'renouveler_1mois', 'renouveler_3mois', 'suspendre_acces', 'remettre_en_essai']

    def plan_badge(self, obj):
        colors = {'essai': '#F59E0B', 'payant': '#22C55E', 'suspendu': '#EF4444'}
        labels = {'essai': 'Essai', 'payant': 'Abonné', 'suspendu': 'Suspendu'}
        c = colors.get(obj.plan, '#6B7280')
        l = labels.get(obj.plan, obj.plan)
        return format_html('<span style="background:{};color:#fff;padding:3px 10px;border-radius:10px;font-size:11px;font-weight:700">{}</span>', c, l)
    plan_badge.short_description = 'Plan'

    def acces_badge(self, obj):
        if obj.acces_actif:
            return format_html('<span style="color:#22C55E;font-weight:700">✓ Actif</span>')
        return format_html('<span style="color:#EF4444;font-weight:700">✗ Bloqué</span>')
    acces_badge.short_description = 'Accès'

    def date_echeance(self, obj):
        d = obj.date_fin_abonnement or obj.date_fin_essai
        if not d:
            return '—'
        from datetime import date
        if d < date.today():
            return format_html('<span style="color:#EF4444;font-weight:600">{}</span>', d.strftime('%d/%m/%Y'))
        return d.strftime('%d/%m/%Y')
    date_echeance.short_description = 'Échéance'

    def date_blocage_auto(self, obj):
        from datetime import date, timedelta
        d = obj.date_fin_abonnement or obj.date_fin_essai
        if not d:
            return '—'
        blocage = d + timedelta(days=obj.GRACE_DAYS)
        if blocage < date.today():
            return format_html('<span style="color:#EF4444;font-weight:700">Expiré</span>')
        jours = (blocage - date.today()).days
        couleur = '#F59E0B' if jours <= 3 else '#94A3B8'
        return format_html('<span style="color:{}">{} (J-{})</span>', couleur, blocage.strftime('%d/%m/%Y'), jours)
    date_blocage_auto.short_description = 'Blocage auto (J-X)'

    def nb_utilisateurs(self, obj):
        return obj.utilisateurs.count()
    nb_utilisateurs.short_description = 'Utilisateurs'

    def nb_transactions(self, obj):
        return obj.transactions.count()
    nb_transactions.short_description = 'Transactions'

    def logo_apercu(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="60" style="border-radius:6px"/>', obj.logo.url)
        return '—'
    logo_apercu.short_description = 'Logo'

    def passer_en_payant_1mois(self, request, queryset):
        from datetime import date, timedelta
        fin = date.today() + timedelta(days=30)
        queryset.update(plan='payant', date_fin_essai=None, date_fin_abonnement=fin)
        self.message_user(request, f'{queryset.count()} entreprise(s) activée(s) — accès jusqu\'au {fin.strftime("%d/%m/%Y")}.')
    passer_en_payant_1mois.short_description = '✅ Activer abonnement (1 mois)'

    def renouveler_1mois(self, request, queryset):
        from datetime import date, timedelta
        today = date.today()
        for entreprise in queryset:
            base = entreprise.date_fin_abonnement if entreprise.date_fin_abonnement and entreprise.date_fin_abonnement > today else today
            entreprise.date_fin_abonnement = base + timedelta(days=30)
            entreprise.plan = 'payant'
            entreprise.save()
        self.message_user(request, f'{queryset.count()} abonnement(s) renouvelé(s) de 30 jours.')
    renouveler_1mois.short_description = '🔄 Renouveler 1 mois'

    def renouveler_3mois(self, request, queryset):
        from datetime import date, timedelta
        today = date.today()
        for entreprise in queryset:
            base = entreprise.date_fin_abonnement if entreprise.date_fin_abonnement and entreprise.date_fin_abonnement > today else today
            entreprise.date_fin_abonnement = base + timedelta(days=90)
            entreprise.plan = 'payant'
            entreprise.save()
        self.message_user(request, f'{queryset.count()} abonnement(s) renouvelé(s) de 90 jours.')
    renouveler_3mois.short_description = '🔄 Renouveler 3 mois'

    def suspendre_acces(self, request, queryset):
        queryset.update(plan='suspendu')
        self.message_user(request, f'{queryset.count()} entreprise(s) suspendue(s).')
    suspendre_acces.short_description = '🚫 Suspendre l\'accès'

    def remettre_en_essai(self, request, queryset):
        from datetime import date, timedelta
        queryset.update(plan='essai', date_fin_essai=date.today() + timedelta(days=30), date_fin_abonnement=None)
        self.message_user(request, f'{queryset.count()} entreprise(s) remise(s) en essai (30 jours).')
    remettre_en_essai.short_description = '🔄 Remettre en essai (30 jours)'
