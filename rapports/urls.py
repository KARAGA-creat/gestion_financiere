from django.urls import path
from .views import RapportListView, RapportGenererView

urlpatterns = [
    path('',          RapportListView.as_view(),   name='rapport-list'),
    path('generer/',  RapportGenererView.as_view(), name='rapport-generer'),
]