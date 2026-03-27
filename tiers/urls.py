from django.urls import path
from .views import TiersListView, TiersDetailView

urlpatterns = [
    path('',          TiersListView.as_view(),   name='tiers-list'),
    path('<int:pk>/', TiersDetailView.as_view(), name='tiers-detail'),
]