from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Entreprise


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display    = ('nom', 'plan_badge', 'date_fin_essai', 'acces_badge', 'devise', 'nb_utilisateurs', 'nb_transactions', 'logo_apercu')
    search_fields   = ('nom',)
    list_filter     = ('plan', 'devise')
    ordering        = ('nom',)
    readonly_fields = ('logo_apercu', 'acces_badge')
    fields          = ('nom', 'logo', 'logo_apercu', 'devise', 'date_creation', 'plan', 'date_fin_essai')
    actions         = ['passer_en_payant', 'suspendre_acces', 'remettre_en_essai']

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

    def passer_en_payant(self, request, queryset):
        queryset.update(plan='payant', date_fin_essai=None)
        self.message_user(request, f'{queryset.count()} entreprise(s) passée(s) en abonné.')
    passer_en_payant.short_description = '✅ Passer en abonné (payant)'

    def suspendre_acces(self, request, queryset):
        queryset.update(plan='suspendu')
        self.message_user(request, f'{queryset.count()} entreprise(s) suspendue(s).')
    suspendre_acces.short_description = '🚫 Suspendre l\'accès'

    def remettre_en_essai(self, request, queryset):
        from datetime import date, timedelta
        queryset.update(plan='essai', date_fin_essai=date.today() + timedelta(days=30))
        self.message_user(request, f'{queryset.count()} entreprise(s) remise(s) en essai (30 jours).')
    remettre_en_essai.short_description = '🔄 Remettre en essai (30 jours)'
