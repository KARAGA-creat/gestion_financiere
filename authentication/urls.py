from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, ProfilView, InscriptionView,
    UtilisateursView, UtilisateurDetailView,
    InviterGestionnaireView, VerifierInvitationView, ActiverCompteView,
)

urlpatterns = [
    path('login/',               LoginView.as_view(),             name='login'),
    path('logout/',              LogoutView.as_view(),             name='logout'),
    path('refresh/',             TokenRefreshView.as_view(),       name='token_refresh'),
    path('profil/',              ProfilView.as_view(),             name='profil'),
    path('inscription/',         InscriptionView.as_view(),        name='inscription'),
    path('utilisateurs/',        UtilisateursView.as_view(),       name='utilisateurs'),
    path('utilisateurs/<int:pk>/', UtilisateurDetailView.as_view(), name='utilisateur-detail'),
    path('invitations/',                          InviterGestionnaireView.as_view(), name='inviter'),
    path('invitations/<uuid:token>/verifier/',    VerifierInvitationView.as_view(),  name='verifier-invitation'),
    path('invitations/<uuid:token>/activer/',     ActiverCompteView.as_view(),       name='activer-compte'),
]