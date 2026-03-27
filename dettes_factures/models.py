from django.db import models
from entreprises.models import Entreprise
from tiers.models import Tiers
from transactions.models import Transaction

class DetteFacture(models.Model):
    TYPE_CHOICES = [
        ('Client',      'Client'),
        ('Fournisseur', 'Fournisseur'),
    ]
    STATUT_CHOICES = [
        ('en_cours',            'En cours'),
        ('partiellement_paye',  'Partiellement payé'),
        ('solde',               'Soldé'),
        ('en_retard',           'En retard'),
    ]

    type          = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant_total = models.DecimalField(max_digits=15, decimal_places=2)
    montant_paye  = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_echeance = models.DateField()
    statut        = models.CharField(max_length=25, choices=STATUT_CHOICES, default='en_cours')
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='dettes')
    id_tiers      = models.ForeignKey(Tiers, on_delete=models.CASCADE, related_name='dettes')
    id_transaction= models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='dettes')

    class Meta:
        db_table = 'dette_facture'
        ordering = ['date_echeance']

    def __str__(self):
        return f"{self.type} - {self.montant_total} XOF ({self.statut})"

    def montant_restant(self):
        return self.montant_total - self.montant_paye