from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Entreprise
from .serializers import EntrepriseSerializer


class EntrepriseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.id_entreprise is None:
            return Response(
                {'error': 'Aucune entreprise liée à cet utilisateur'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            entreprise = Entreprise.objects.get(
                id=request.user.id_entreprise.id
            )
            serializer = EntrepriseSerializer(entreprise)
            return Response(serializer.data)
        except Entreprise.DoesNotExist:
            return Response(
                {'error': 'Entreprise non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        if request.user.id_entreprise is None:
            return Response(
                {'error': 'Aucune entreprise liée à cet utilisateur'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            entreprise = Entreprise.objects.get(
                id=request.user.id_entreprise.id
            )
            serializer = EntrepriseSerializer(
                entreprise,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Entreprise.DoesNotExist:
            return Response(
                {'error': 'Entreprise non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )