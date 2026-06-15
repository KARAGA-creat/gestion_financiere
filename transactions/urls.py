from django.urls import path
from .views import TransactionListView, TransactionDetailView, TransactionExportView, DashboardStatsView

urlpatterns = [
    path('',          TransactionListView.as_view(),   name='transaction-list'),
    path('stats/',    DashboardStatsView.as_view(),    name='transaction-stats'),
    path('export/',   TransactionExportView.as_view(), name='transaction-export'),
    path('<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
]