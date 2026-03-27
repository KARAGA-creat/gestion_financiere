from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Tiers
from .serializers import TiersSerializer

class TiersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tiers = Tiers.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = TiersSerializer(tiers, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['id_entreprise'] = request.user.id_entreprise.id
        serializer = TiersSerializer(data=data)
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


class TiersDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            tiers = Tiers.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            serializer = TiersSerializer(
                tiers,
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
        except Tiers.DoesNotExist:
            return Response(
                {'error': 'Tiers non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            tiers = Tiers.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            tiers.delete()
            return Response(
                {'message': 'Tiers supprimé !'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Tiers.DoesNotExist:
            return Response(
                {'error': 'Tiers non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )