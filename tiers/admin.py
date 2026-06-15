from django.contrib import admin
from .models import Tiers


@admin.register(Tiers)
class TiersAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'type', 'email', 'telephone', 'id_entreprise')
    list_filter   = ('type', 'id_entreprise')
    search_fields = ('nom', 'email', 'id_entreprise__nom')
    ordering      = ('nom',)
