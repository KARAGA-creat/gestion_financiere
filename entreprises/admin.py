from django.contrib import admin
from django.utils.html import format_html
from .models import Entreprise


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display    = ('nom', 'devise', 'date_creation', 'nb_utilisateurs', 'nb_transactions', 'logo_apercu')
    search_fields   = ('nom',)
    list_filter     = ('devise', 'date_creation')
    ordering        = ('nom',)
    readonly_fields = ('logo_apercu',)

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
