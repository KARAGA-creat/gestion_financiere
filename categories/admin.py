from django.contrib import admin
from .models import Categorie


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display  = ('nom_categorie', 'id_entreprise')
    list_filter   = ('id_entreprise',)
    search_fields = ('nom_categorie', 'id_entreprise__nom')
    ordering      = ('id_entreprise', 'nom_categorie')
