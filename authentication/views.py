import time
from django.shortcuts import render
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from threading import Thread

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, UtilisateurSerializer, InscriptionSerializer
from .permissions import IsAdminRole

_MAX_ATTEMPTS = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
_LOCK_SECONDS = getattr(settings, 'LOGIN_LOCK_SECONDS', 900)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ip          = _get_client_ip(request)
        attempt_key = f'login_attempts_{ip}'
        block_key   = f'login_block_until_{ip}'

        # Vérifier si l'IP est bloquée
        block_until = cache.get(block_key)
        if block_until:
            remaining = max(0, int(block_until - time.time()))
            minutes   = remaining // 60 + 1
            return Response({
                'error': f'Trop de tentatives échouées. Réessayez dans environ {minutes} minute(s).',
                'bloque': True,
                'attente_secondes': remaining,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            # Vérifier que l'accès de l'entreprise est actif
            if user.id_entreprise and not user.id_entreprise.acces_actif:
                return Response(
                    {'error': 'acces_expire', 'acces_expire': True},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Succès : on efface les compteurs
            cache.delete(attempt_key)
            cache.delete(block_key)
            refresh = RefreshToken.for_user(user)
            return Response({
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user':    UtilisateurSerializer(user).data
            }, status=status.HTTP_200_OK)

        # Échec : incrémenter le compteur
        attempts = cache.get(attempt_key, 0) + 1
        cache.set(attempt_key, attempts, _LOCK_SECONDS)

        if attempts >= _MAX_ATTEMPTS:
            cache.set(block_key, time.time() + _LOCK_SECONDS, _LOCK_SECONDS)
            return Response({
                'error': f'Compte bloqué 15 minutes après {_MAX_ATTEMPTS} tentatives échouées.',
                'bloque': True,
                'attente_secondes': _LOCK_SECONDS,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        remaining_attempts = _MAX_ATTEMPTS - attempts
        return Response({
            'error': f'Identifiants incorrects. {remaining_attempts} tentative(s) restante(s) avant blocage.',
            'tentatives_restantes': remaining_attempts,
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {'message': 'Déconnexion réussie !'},
            status=status.HTTP_200_OK
        )


class ProfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)


class InscriptionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InscriptionSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Compte créé avec succès !',
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user':    UtilisateurSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UtilisateursView(APIView):

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def get(self, request):
        """Liste tous les utilisateurs de la même entreprise."""
        from .models import Utilisateur
        users = Utilisateur.objects.filter(id_entreprise=request.user.id_entreprise)
        serializer = UtilisateurSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Crée un nouveau gestionnaire dans la même entreprise."""
        from .models import Utilisateur
        username = request.data.get('username', '').strip()
        email    = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not username or not email or not password:
            return Response({'error': 'username, email et password sont requis.'}, status=status.HTTP_400_BAD_REQUEST)

        if Utilisateur.objects.filter(username=username).exists():
            return Response({'error': "Ce nom d'utilisateur existe déjà."}, status=status.HTTP_400_BAD_REQUEST)

        if Utilisateur.objects.filter(email=email).exists():
            return Response({'error': 'Cet email est déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({'error': 'Le mot de passe doit contenir au moins 6 caractères.'}, status=status.HTTP_400_BAD_REQUEST)

        user = Utilisateur.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='gestionnaire',
            id_entreprise=request.user.id_entreprise,
        )
        return Response(UtilisateurSerializer(user).data, status=status.HTTP_201_CREATED)


class UtilisateurDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, pk):
        """Basculer le statut actif / inactif d'un utilisateur."""
        from .models import Utilisateur
        try:
            user = Utilisateur.objects.get(pk=pk, id_entreprise=request.user.id_entreprise)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        if user.pk == request.user.pk:
            return Response({'error': 'Vous ne pouvez pas modifier votre propre statut.'}, status=status.HTTP_400_BAD_REQUEST)

        user.statut = 'inactif' if user.statut == 'actif' else 'actif'
        user.save()
        return Response(UtilisateurSerializer(user).data)

    def delete(self, request, pk):
        """Supprimer un gestionnaire (impossible de supprimer un admin ou soi-même)."""
        from .models import Utilisateur
        try:
            user = Utilisateur.objects.get(pk=pk, id_entreprise=request.user.id_entreprise)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        if user.pk == request.user.pk:
            return Response({'error': 'Vous ne pouvez pas supprimer votre propre compte.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.role == 'admin':
            return Response({'error': 'Impossible de supprimer un administrateur.'}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({'message': 'Utilisateur supprimé.'}, status=status.HTTP_204_NO_CONTENT)


class InviterGestionnaireView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        from .models import Invitation, Utilisateur
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email requis.'}, status=status.HTTP_400_BAD_REQUEST)

        if Utilisateur.objects.filter(email=email).exists():
            return Response({'error': 'Un compte existe déjà avec cet email.'}, status=status.HTTP_400_BAD_REQUEST)

        # Supprimer toute invitation non utilisée existante pour cet email + entreprise
        Invitation.objects.filter(
            email=email,
            id_entreprise=request.user.id_entreprise,
            is_used=False
        ).delete()

        invitation = Invitation.objects.create(
            email=email,
            id_entreprise=request.user.id_entreprise,
            created_by=request.user,
        )

        lien           = f"{settings.FRONTEND_URL}/activation/{invitation.token}"
        nom_entreprise = request.user.id_entreprise.nom
        invite_par     = request.user.username

        sujet = f"Vous êtes invité(e) à rejoindre {nom_entreprise} sur FinanceIQ"
        corps = (
            f"Bonjour,\n\n"
            f"{invite_par}, responsable de {nom_entreprise}, vous invite à rejoindre "
            f"l'espace FinanceIQ de l'entreprise en tant que Gestionnaire.\n\n"
            f"FinanceIQ est une application de gestion financière qui vous permettra "
            f"de suivre les transactions, les dettes et les budgets de {nom_entreprise}.\n\n"
            f"─────────────────────────────\n"
            f"Créer votre accès :\n"
            f"{lien}\n"
            f"─────────────────────────────\n\n"
            f"⚠️  Ce lien est personnel et valable 48 heures.\n"
            f"Ne le partagez avec personne.\n\n"
            f"Si vous n'attendiez pas cette invitation, ignorez simplement cet email.\n\n"
            f"Bienvenue dans l'équipe,\n"
            f"L'équipe FinanceIQ"
        )

        def _envoyer():
            try:
                send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
            except Exception:
                pass

        Thread(target=_envoyer, daemon=True).start()

        return Response({'message': f'Invitation envoyée à {email}.'}, status=status.HTTP_201_CREATED)


class VerifierInvitationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        from .models import Invitation
        try:
            inv = Invitation.objects.select_related('id_entreprise').get(token=token)
        except Invitation.DoesNotExist:
            return Response({'error': 'Lien invalide.'}, status=status.HTTP_404_NOT_FOUND)

        if not inv.is_valid:
            return Response({'error': 'Ce lien a expiré ou a déjà été utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'email':       inv.email,
            'entreprise':  inv.id_entreprise.nom,
            'expires_at':  inv.expires_at,
        })


class ActiverCompteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        from .models import Invitation, Utilisateur
        try:
            inv = Invitation.objects.select_related('id_entreprise').get(token=token)
        except Invitation.DoesNotExist:
            return Response({'error': 'Lien invalide.'}, status=status.HTTP_404_NOT_FOUND)

        if not inv.is_valid:
            return Response({'error': 'Ce lien a expiré ou a déjà été utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response({'error': 'Nom d\'utilisateur et mot de passe requis.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({'error': 'Le mot de passe doit contenir au moins 6 caractères.'}, status=status.HTTP_400_BAD_REQUEST)

        if Utilisateur.objects.filter(username=username).exists():
            return Response({'error': "Ce nom d'utilisateur existe déjà."}, status=status.HTTP_400_BAD_REQUEST)

        user = Utilisateur.objects.create_user(
            username=username,
            email=inv.email,
            password=password,
            role='gestionnaire',
            id_entreprise=inv.id_entreprise,
        )

        inv.is_used = True
        inv.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UtilisateurSerializer(user).data,
        }, status=status.HTTP_201_CREATED)