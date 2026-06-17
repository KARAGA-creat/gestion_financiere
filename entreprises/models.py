from django.db import models
from django.utils import timezone


class Entreprise(models.Model):
    DEVISE_CHOICES = [
        ('XOF', 'Franc CFA (UEMOA)'),
        ('GNF', 'Franc Guinéen'),
        ('MAD', 'Dirham Marocain'),
        ('EUR', 'Euro'),
        ('USD', 'Dollar Américain'),
        ('XAF', 'Franc CFA (CEMAC)'),
    ]
    PLAN_CHOICES = [
        ('essai',    'Période d\'essai'),
        ('payant',   'Abonné'),
        ('suspendu', 'Suspendu'),
    ]

    nom            = models.CharField(max_length=150)
    logo           = models.ImageField(upload_to='logos/', blank=True, null=True)
    devise         = models.CharField(max_length=10, choices=DEVISE_CHOICES, default='XOF')
    date_creation  = models.DateField()
    plan           = models.CharField(max_length=20, choices=PLAN_CHOICES, default='essai')
    date_fin_essai = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'entreprise'

    @property
    def acces_actif(self):
        if self.plan == 'payant':
            return True
        if self.plan == 'suspendu':
            return False
        # essai : vérifie la date
        if self.date_fin_essai and timezone.now().date() > self.date_fin_essai:
            return False
        return True

    def __str__(self):
        return self.nom
