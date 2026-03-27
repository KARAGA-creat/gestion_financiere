from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Utilisateur

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