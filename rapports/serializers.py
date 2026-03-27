from rest_framework import serializers
from .models import RapportSnapshot

class RapportSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RapportSnapshot
        fields = '__all__'