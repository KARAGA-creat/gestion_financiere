from rest_framework import serializers
from .models import Tiers

class TiersSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tiers
        fields = '__all__'