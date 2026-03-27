from django.db import models
from entreprises.models import Entreprise

class Categorie(models.Model):
    nom_categorie = models.CharField(max_length=100)
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='categories')

    class Meta:
        db_table = 'categorie'
        unique_together = ['nom_categorie', 'id_entreprise']

    def __str__(self):
        return self.nom_categorie