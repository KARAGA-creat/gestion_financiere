from django.db import models
from entreprises.models import Entreprise
from authentication.models import Utilisateur
from categories.models import Categorie

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('Entree', 'Entrée'),
        ('Sortie', 'Sortie'),
    ]
    STATUT_CHOICES = [
        ('validee',    'Validée'),
        ('en_attente', 'En attente'),
    ]

    type             = models.CharField(max_length=10, choices=TYPE_CHOICES)
    montant          = models.DecimalField(max_digits=15, decimal_places=2)
    date_transaction = models.DateField()
    libelle          = models.CharField(max_length=255, blank=True, null=True)
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='validee')
    piece_jointe     = models.FileField(upload_to='pieces_jointes/', blank=True, null=True)
    id_entreprise    = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='transactions')
    id_utilisateur   = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='transactions')
    id_categorie     = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='transactions')

    class Meta:
        db_table = 'transaction'
        ordering = ['-date_transaction']

    def __str__(self):
        return f"{self.type} - {self.montant} XOF"
