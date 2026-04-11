from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Utilisateur
from entreprises.models import Entreprise

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password']
        )
        if not user:
            raise serializers.ValidationError("Identifiants incorrects !")
        if user.statut == 'inactif':
            raise serializers.ValidationError("Compte désactivé !")
        return user


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Utilisateur
        fields = ['id', 'username', 'email', 'role', 'statut']
       
class InscriptionSerializer(serializers.Serializer):
    # Infos utilisateur
    username  = serializers.CharField(max_length=150)
    email     = serializers.EmailField()
    password  = serializers.CharField(write_only=True, min_length=6)

    # Infos entreprise
    nom_entreprise = serializers.CharField(max_length=150)
    devise         = serializers.ChoiceField(choices=[
        ('XOF', 'XOF'), ('GNF', 'GNF'),
        ('EUR', 'EUR'), ('USD', 'USD'), ('MAD', 'MAD'),
    ])
    date_creation  = serializers.DateField()

    def validate_username(self, value):
        if Utilisateur.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur existe déjà !"
            )
        return value

    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Cet email est déjà utilisé !"
            )
        return value

    def create(self, validated_data):
        # Créer l'entreprise
        entreprise = Entreprise.objects.create(
            nom=validated_data['nom_entreprise'],
            devise=validated_data['devise'],
            date_creation=validated_data['date_creation'],
        )

        # Créer l'utilisateur Admin
        user = Utilisateur.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='admin',
            id_entreprise=entreprise,
        )

        return user  