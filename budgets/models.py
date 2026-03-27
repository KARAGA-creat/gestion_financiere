from django.db import models
from entreprises.models import Entreprise
from categories.models import Categorie

class Budget(models.Model):
    montant_limite   = models.DecimalField(max_digits=15, decimal_places=2)
    date_debut       = models.DateField()
    date_fin         = models.DateField()
    montant_consomme = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    id_entreprise    = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='budgets')
    id_categorie     = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='budgets')

    class Meta:
        db_table = 'budget'
        ordering = ['date_fin']

    def __str__(self):
        return f"Budget {self.id_categorie} - {self.montant_limite} XOF"

    def taux_consommation(self):
        if self.montant_limite == 0:
            return 0
        return round((self.montant_consomme / self.montant_limite) * 100, 2)

    def is_depasse(self):
        return self.montant_consomme > self.montant_limite