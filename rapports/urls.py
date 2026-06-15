from django.urls import path
from .views import RapportListView, RapportGenererView, RapportExportPDFView

urlpatterns = [
    path('',        RapportListView.as_view(),    name='rapport-list'),
    path('generer/', RapportGenererView.as_view(), name='rapport-generer'),
    path('pdf/',    RapportExportPDFView.as_view(), name='rapport-pdf'),
]
