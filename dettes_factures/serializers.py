from rest_framework import serializers
from .models import DetteFacture

class DetteFactureSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DetteFacture
        fields = '__all__'