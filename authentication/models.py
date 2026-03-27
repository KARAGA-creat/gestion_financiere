from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models
from entreprises.models import Entreprise

class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('admin',        'Administrateur'),
        ('comptable',    'Comptable'),
        ('gestionnaire', 'Gestionnaire'),
    ]
    STATUT_CHOICES = [
        ('actif',   'Actif'),
        ('inactif', 'Inactif'),
    ]

    role          = models.CharField(max_length=20, choices=ROLE_CHOICES, default='gestionnaire')
    statut        = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='utilisateurs', null=True, blank=True)

    class Meta:
        db_table = 'utilisateur'

    def __str__(self):
        return f"{self.username} ({self.role})"
