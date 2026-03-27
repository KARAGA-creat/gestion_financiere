from django.urls import path
from .views import CategorieListView, CategorieDetailView

urlpatterns = [
    path('',      CategorieListView.as_view(),   name='categorie-list'),
    path('<int:pk>/', CategorieDetailView.as_view(), name='categorie-detail'),
]