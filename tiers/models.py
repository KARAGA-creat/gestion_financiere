from django.db import models
from entreprises.models import Entreprise

class Tiers(models.Model):
    TYPE_CHOICES = [
        ('Client',      'Client'),
        ('Fournisseur', 'Fournisseur'),
    ]

    nom           = models.CharField(max_length=150)
    email         = models.EmailField(blank=True, null=True)
    telephone     = models.CharField(max_length=20, blank=True, null=True)
    adresse       = models.TextField(blank=True, null=True)
    type          = models.CharField(max_length=20, choices=TYPE_CHOICES)
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='tiers')

    class Meta:
        db_table = 'tiers'

    def __str__(self):
        return f"{self.nom} ({self.type})"