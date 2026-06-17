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

    nom                  = models.CharField(max_length=150)
    logo                 = models.ImageField(upload_to='logos/', blank=True, null=True)
    devise               = models.CharField(max_length=10, choices=DEVISE_CHOICES, default='XOF')
    date_creation        = models.DateField()
    plan                 = models.CharField(max_length=20, choices=PLAN_CHOICES, default='essai')
    date_fin_essai       = models.DateField(null=True, blank=True)
    date_fin_abonnement  = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'entreprise'

    GRACE_DAYS = 5  # jours de grâce après échéance avant blocage automatique

    @property
    def acces_actif(self):
        from datetime import timedelta
        today = timezone.now().date()
        grace = timedelta(days=self.GRACE_DAYS)
        if self.plan == 'suspendu':
            return False
        if self.plan == 'essai':
            if self.date_fin_essai and today > self.date_fin_essai + grace:
                return False
            return True
        if self.plan == 'payant':
            if self.date_fin_abonnement and today > self.date_fin_abonnement + grace:
                return False
            return True
        return True

    def __str__(self):
        return self.nom
