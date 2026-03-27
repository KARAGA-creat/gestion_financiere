from django.db import models
from entreprises.models import Entreprise

class RapportSnapshot(models.Model):
    mois          = models.PositiveSmallIntegerField()
    annee         = models.PositiveSmallIntegerField()
    total_entrees = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sorties = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    solde_final   = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='rapports')

    class Meta:
        db_table = 'rapport_snapshot'
        ordering = ['-annee', '-mois']
        unique_together = ['id_entreprise', 'mois', 'annee']

    def __str__(self):
        return f"Rapport {self.mois}/{self.annee}"