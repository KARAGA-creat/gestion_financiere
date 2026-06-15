from django.urls import path
from .views import DetteFactureListView, DetteFactureDetailView, RappelDetteView

urlpatterns = [
    path('',                    DetteFactureListView.as_view(),   name='dette-list'),
    path('<int:pk>/',           DetteFactureDetailView.as_view(), name='dette-detail'),
    path('<int:pk>/rappel/',    RappelDetteView.as_view(),        name='dette-rappel'),
]