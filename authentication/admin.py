from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display   = ('username', 'email', 'id_entreprise', 'role', 'statut_badge', 'date_joined')
    list_filter    = ('role', 'statut', 'id_entreprise', 'is_active')
    search_fields  = ('username', 'email', 'id_entreprise__nom')
    ordering       = ('-date_joined',)
    actions        = ['activer_comptes', 'desactiver_comptes']

    fieldsets = UserAdmin.fieldsets + (
        ('Informations entreprise', {
            'fields': ('id_entreprise', 'role', 'statut')
        }),
    )

    def statut_badge(self, obj):
        color = '#28a745' if obj.statut == 'actif' else '#dc3545'
        return format_html('<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>', color, obj.statut.capitalize())
    statut_badge.short_description = 'Statut'

    def activer_comptes(self, request, queryset):
        queryset.update(statut='actif', is_active=True)
        self.message_user(request, f'{queryset.count()} compte(s) active(s).')
    activer_comptes.short_description = 'Activer les comptes selectionnes'

    def desactiver_comptes(self, request, queryset):
        queryset.update(statut='inactif', is_active=False)
        self.message_user(request, f'{queryset.count()} compte(s) desactive(s).')
    desactiver_comptes.short_description = 'Desactiver les comptes selectionnes'
