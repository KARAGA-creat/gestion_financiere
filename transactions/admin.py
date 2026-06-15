from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display   = ('libelle', 'type_badge', 'montant', 'id_categorie', 'id_entreprise', 'statut', 'date_transaction')
    list_filter    = ('type', 'statut', 'id_entreprise', 'date_transaction')
    search_fields  = ('libelle', 'id_entreprise__nom', 'id_categorie__nom_categorie')
    ordering       = ('-date_transaction',)
    date_hierarchy = 'date_transaction'

    def type_badge(self, obj):
        color = '#28a745' if obj.type == 'Entree' else '#dc3545'
        label = 'Entree' if obj.type == 'Entree' else 'Sortie'
        return format_html('<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>', color, label)
    type_badge.short_description = 'Type'
