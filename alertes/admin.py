from django.contrib import admin
from .models import Alerte


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display    = ('type_alerte', 'id_entreprise', 'statut', 'date_emission')
    list_filter     = ('type_alerte', 'statut', 'id_entreprise')
    search_fields   = ('message', 'id_entreprise__nom')
    ordering        = ('-date_emission',)
    readonly_fields = ('message', 'date_emission', 'type_alerte', 'id_entreprise', 'id_utilisateur')
    actions         = ['marquer_lues']

    def marquer_lues(self, request, queryset):
        queryset.update(statut='lue')
        self.message_user(request, f'{queryset.count()} alerte(s) marquee(s) comme lue(s).')
    marquer_lues.short_description = 'Marquer comme lues'
