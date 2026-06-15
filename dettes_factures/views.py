from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from threading import Thread
import datetime
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


class RappelDetteView(APIView):
    """Envoie un email de rappel pour une dette — au tiers si email dispo, et au propriétaire."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            dette = DetteFacture.objects.select_related(
                'id_tiers', 'id_entreprise'
            ).get(pk=pk, id_entreprise=request.user.id_entreprise)
        except DetteFacture.DoesNotExist:
            return Response({'error': 'Dette non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        if dette.statut == 'solde':
            return Response({'error': 'Cette dette est déjà soldée.'}, status=status.HTTP_400_BAD_REQUEST)

        tiers       = dette.id_tiers
        entreprise  = dette.id_entreprise
        restant     = float(dette.montant_total) - float(dette.montant_paye or 0)
        echeance    = dette.date_echeance.strftime('%d/%m/%Y')
        emails_dest = []

        if dette.type == 'Client':
            # Rappel au client qui nous doit de l'argent
            if tiers.email:
                sujet_client = f"Rappel de paiement — {entreprise.nom}"
                corps_client = (
                    f"Bonjour {tiers.nom},\n\n"
                    f"Nous vous contactons au nom de {entreprise.nom} pour vous rappeler "
                    f"qu'un paiement est en attente de règlement.\n\n"
                    f"— Montant total    : {float(dette.montant_total):,.0f} XOF\n"
                    f"— Déjà réglé       : {float(dette.montant_paye or 0):,.0f} XOF\n"
                    f"— Reste à payer    : {restant:,.0f} XOF\n"
                    f"— Date d'échéance  : {echeance}\n\n"
                    f"Merci de bien vouloir procéder au règlement dans les meilleurs délais.\n\n"
                    f"Cordialement,\n{entreprise.nom}"
                )
                emails_dest.append((sujet_client, corps_client, tiers.email))

            # Copie au propriétaire
            if request.user.email:
                sujet_owner = f"[FinanceIQ] Rappel envoyé à {tiers.nom}"
                corps_owner = (
                    f"Bonjour {request.user.username},\n\n"
                    f"Un rappel de paiement a été envoyé à votre client {tiers.nom}.\n\n"
                    f"— Restant dû  : {restant:,.0f} XOF\n"
                    f"— Échéance    : {echeance}\n"
                    + (f"— Email envoyé à : {tiers.email}\n" if tiers.email
                       else "— Aucun email client enregistré — rappel non envoyé au client.\n")
                    + f"\nFinanceIQ"
                )
                emails_dest.append((sujet_owner, corps_owner, request.user.email))

        else:
            # Rappel au propriétaire qu'il doit payer un fournisseur
            if request.user.email:
                sujet = f"[FinanceIQ] Rappel : paiement dû à {tiers.nom}"
                corps = (
                    f"Bonjour {request.user.username},\n\n"
                    f"Ceci est un rappel : vous avez un paiement en attente auprès de {tiers.nom}.\n\n"
                    f"— Montant total    : {float(dette.montant_total):,.0f} XOF\n"
                    f"— Déjà payé        : {float(dette.montant_paye or 0):,.0f} XOF\n"
                    f"— Reste à payer    : {restant:,.0f} XOF\n"
                    f"— Date d'échéance  : {echeance}\n\n"
                    f"Pensez à régulariser ce paiement pour maintenir de bonnes relations "
                    f"avec votre fournisseur.\n\nFinanceIQ"
                )
                emails_dest.append((sujet, corps, request.user.email))

        if not emails_dest:
            return Response(
                {'warning': 'Aucun email disponible. Ajoutez un email à ce tiers dans la page Tiers.'},
                status=status.HTTP_200_OK
            )

        def _envoyer():
            for sujet, corps, dest in emails_dest:
                try:
                    send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, [dest], fail_silently=True)
                except Exception:
                    pass

        Thread(target=_envoyer, daemon=True).start()

        msg = "Rappel envoyé"
        if dette.type == 'Client' and tiers.email:
            msg += f" à {tiers.nom} ({tiers.email})"
        if request.user.email:
            msg += f" — copie à {request.user.email}"

        return Response({'message': msg + '.'}, status=status.HTTP_200_OK)