from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import RapportSnapshot
from .serializers import RapportSnapshotSerializer
from transactions.models import Transaction
from django.db.models import Sum

class RapportListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rapports = RapportSnapshot.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = RapportSnapshotSerializer(rapports, many=True)
        return Response(serializer.data)


class RapportGenererView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mois  = request.data.get('mois')
        annee = request.data.get('annee')

        if not mois or not annee:
            return Response(
                {'error': 'Mois et année sont obligatoires !'},
                status=status.HTTP_400_BAD_REQUEST
            )

        entreprise = request.user.id_entreprise

        # Calculer total entrées
        total_entrees = Transaction.objects.filter(
            id_entreprise=entreprise,
            type='Entree',
            date_transaction__month=mois,
            date_transaction__year=annee
        ).aggregate(total=Sum('montant'))['total'] or 0

        # Calculer total sorties
        total_sorties = Transaction.objects.filter(
            id_entreprise=entreprise,
            type='Sortie',
            date_transaction__month=mois,
            date_transaction__year=annee
        ).aggregate(total=Sum('montant'))['total'] or 0

        # Calculer solde final
        solde_final = total_entrees - total_sorties

        # Créer ou mettre à jour le rapport
        rapport, created = RapportSnapshot.objects.update_or_create(
            id_entreprise=entreprise,
            mois=mois,
            annee=annee,
            defaults={
                'total_entrees': total_entrees,
                'total_sorties': total_sorties,
                'solde_final':   solde_final,
            }
        )

        serializer = RapportSnapshotSerializer(rapport)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )