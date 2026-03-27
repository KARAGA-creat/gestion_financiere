from django.db import models

class Entreprise(models.Model):
    DEVISE_CHOICES = [
        ('XOF', 'Franc CFA (UEMOA)'),
        ('GNF', 'Franc Guinéen'),
        ('MAD', 'Dirham Marocain'),
        ('EUR', 'Euro'),
        ('USD', 'Dollar Américain'),
        ('XAF', 'Franc CFA (CEMAC)'),
    ]

    nom           = models.CharField(max_length=150)
    logo          = models.ImageField(upload_to='logos/', blank=True, null=True)
    devise        = models.CharField(max_length=10, choices=DEVISE_CHOICES, default='XOF')
    date_creation = models.DateField()

    class Meta:
        db_table = 'entreprise'

    def __str__(self):
        return self.nom
