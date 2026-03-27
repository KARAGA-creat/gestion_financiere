from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Alerte
from .serializers import AlerteSerializer

class AlerteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alertes = Alerte.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = AlerteSerializer(alertes, many=True)
        return Response(serializer.data)


class AlerteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            alerte = Alerte.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            alerte.statut = 'lue'
            alerte.save()
            return Response(
                {'message': 'Alerte marquée comme lue !'},
                status=status.HTTP_200_OK
            )
        except Alerte.DoesNotExist:
            return Response(
                {'error': 'Alerte non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )