from django.urls import path
from .views import EntrepriseDetailView

urlpatterns = [
    path('', EntrepriseDetailView.as_view(), name='entreprise-detail'),
]