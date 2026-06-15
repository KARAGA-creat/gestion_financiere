from django.contrib import admin
from .models import RapportSnapshot


@admin.register(RapportSnapshot)
class RapportSnapshotAdmin(admin.ModelAdmin):
    list_display    = ('periode', 'id_entreprise', 'total_entrees', 'total_sorties', 'solde_final')
    list_filter     = ('id_entreprise', 'annee', 'mois')
    ordering        = ('-annee', '-mois')
    readonly_fields = ('mois', 'annee', 'total_entrees', 'total_sorties', 'solde_final', 'id_entreprise')

    def periode(self, obj):
        mois_noms = ['', 'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre']
        return f'{mois_noms[obj.mois]} {obj.annee}'
    periode.short_description = 'Periode'
