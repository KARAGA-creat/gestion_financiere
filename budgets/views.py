from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Budget
from .serializers import BudgetSerializer

class BudgetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        budgets = Budget.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['id_entreprise'] = request.user.id_entreprise.id
        serializer = BudgetSerializer(data=data)
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


class BudgetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            budget = Budget.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            serializer = BudgetSerializer(
                budget,
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
        except Budget.DoesNotExist:
            return Response(
                {'error': 'Budget non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            budget = Budget.objects.get(
                pk=pk,
                id_entreprise=request.user.id_entreprise
            )
            budget.delete()
            return Response(
                {'message': 'Budget supprimé !'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Budget.DoesNotExist:
            return Response(
                {'error': 'Budget non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )