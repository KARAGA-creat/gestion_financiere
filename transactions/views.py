from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Transaction
from .serializers import TransactionSerializer

class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['id_entreprise']  = request.user.id_entreprise.id
        data['id_utilisateur'] = request.user.id
        serializer = TransactionSerializer(data=data)
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


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            transaction = Transaction.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            serializer = TransactionSerializer(
                transaction,
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
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            transaction = Transaction.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            transaction.delete()
            return Response(
                {'message': 'Transaction supprimée !'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )