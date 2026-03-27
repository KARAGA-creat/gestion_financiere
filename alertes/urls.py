from django.urls import path
from .views import AlerteListView, AlerteDetailView

urlpatterns = [
    path('',               AlerteListView.as_view(),   name='alerte-list'),
    path('<int:pk>/lue/',  AlerteDetailView.as_view(), name='alerte-lue'),
]