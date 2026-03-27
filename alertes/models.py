from django.db import models
from entreprises.models import Entreprise
from authentication.models import Utilisateur

class Alerte(models.Model):
    TYPE_CHOICES = [
        ('depassement_budget',  'Dépassement de budget'),
        ('baisse_tresorerie',   'Baisse de trésorerie'),
        ('echeance_dette',      'Échéance de dette'),
        ('anomalie',            'Anomalie'),
    ]
    STATUT_CHOICES = [
        ('lue',     'Lue'),
        ('non_lue', 'Non lue'),
    ]

    message       = models.TextField()
    date_emission = models.DateTimeField(auto_now_add=True)
    type_alerte   = models.CharField(max_length=30, choices=TYPE_CHOICES)
    statut        = models.CharField(max_length=10, choices=STATUT_CHOICES, default='non_lue')
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='alertes')
    id_utilisateur= models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='alertes')

    class Meta:
        db_table = 'alerte'
        ordering = ['-date_emission']

    def __str__(self):
        return f"{self.type_alerte} - {self.statut}"