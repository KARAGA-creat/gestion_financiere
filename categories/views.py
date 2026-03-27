from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Categorie
from .serializers import CategorieSerializer

class CategorieListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Categorie.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = CategorieSerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['id_entreprise'] = request.user.id_entreprise.id
        serializer = CategorieSerializer(data=data)
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


class CategorieDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            categorie = Categorie.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            categorie.delete()
            return Response(
                {'message': 'Catégorie supprimée !'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Categorie.DoesNotExist:
            return Response(
                {'error': 'Catégorie non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )