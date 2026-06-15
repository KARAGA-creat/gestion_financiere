from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import uuid
from entreprises.models import Entreprise


class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('admin',        'Administrateur'),
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


def _expiry_48h():
    return timezone.now() + timedelta(hours=48)


class Invitation(models.Model):
    email         = models.EmailField()
    token         = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    id_entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='invitations')
    created_by    = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='invitations_envoyees')
    expires_at    = models.DateTimeField(default=_expiry_48h)
    is_used       = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invitation'

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Invitation {self.email} → {self.id_entreprise}"
