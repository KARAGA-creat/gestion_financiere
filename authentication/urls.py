from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, LogoutView, ProfilView
from .views import LoginView, LogoutView, ProfilView, InscriptionView

urlpatterns = [
    path('login/',   LoginView.as_view(),   name='login'),
    path('logout/',  LogoutView.as_view(),  name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profil/',  ProfilView.as_view(),  name='profil'),
    path('inscription/', InscriptionView.as_view(), name='inscription'),  # ← nouveau

]