from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur

class UtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informations entreprise', {
            'fields': ('id_entreprise', 'role', 'statut')
        }),
    )

admin.site.register(Utilisateur, UtilisateurAdmin)