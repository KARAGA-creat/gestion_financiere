from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import DetteFacture
from .serializers import DetteFactureSerializer

class DetteFactureListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dettes = DetteFacture.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = DetteFactureSerializer(dettes, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['id_entreprise'] = request.user.id_entreprise.id
        serializer = DetteFactureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class DetteFactureDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            dette = DetteFacture.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            serializer = DetteFactureSerializer(
                dette,
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
        except DetteFacture.DoesNotExist:
            return Response(
                {'error': 'Dette/Facture non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            dette = DetteFacture.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            dette.delete()
            return Response(
                {'message': 'Dette/Facture supprimée !'},
                status=status.HTTP_204_NO_CONTENT
            )
        except DetteFacture.DoesNotExist:
            return Response(
                {'error': 'Dette/Facture non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )