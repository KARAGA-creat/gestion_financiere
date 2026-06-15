from django.contrib import admin
from django.utils.html import format_html
from .models import DetteFacture


@admin.register(DetteFacture)
class DetteFactureAdmin(admin.ModelAdmin):
    list_display  = ('id_tiers', 'type', 'montant_total', 'montant_paye', 'restant', 'statut_badge', 'date_echeance', 'id_entreprise')
    list_filter   = ('type', 'statut', 'id_entreprise', 'date_echeance')
    search_fields = ('id_tiers__nom', 'id_entreprise__nom')
    ordering      = ('date_echeance',)
    date_hierarchy = 'date_echeance'

    def restant(self, obj):
        return obj.montant_restant()
    restant.short_description = 'Restant'

    def statut_badge(self, obj):
        colors = {'en_cours': '#fd7e14', 'partiellement_paye': '#ffc107', 'solde': '#28a745', 'en_retard': '#dc3545'}
        labels = {'en_cours': 'En cours', 'partiellement_paye': 'Part. paye', 'solde': 'Solde', 'en_retard': 'En retard'}
        color = colors.get(obj.statut, '#6c757d')
        label = labels.get(obj.statut, obj.statut)
        return format_html('<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>', color, label)
    statut_badge.short_description = 'Statut'
