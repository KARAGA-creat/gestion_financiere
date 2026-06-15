from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display  = ('id_categorie', 'id_entreprise', 'montant_limite', 'montant_consomme', 'taux_pct', 'date_debut', 'date_fin')
    list_filter   = ('id_entreprise', 'date_fin')
    search_fields = ('id_categorie__nom_categorie', 'id_entreprise__nom')
    ordering      = ('date_fin',)

    def taux_pct(self, obj):
        taux = obj.taux_consommation()
        return f'{taux} %'
    taux_pct.short_description = 'Consommation'
