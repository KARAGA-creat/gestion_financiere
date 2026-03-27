from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/entreprises/', include('entreprises.urls')), 
    path('api/categories/',  include('categories.urls')),
    path('api/tiers/',       include('tiers.urls')),
    path('api/transactions/',  include('transactions.urls')),
    path('api/dettes/',         include('dettes_factures.urls')),
    path('api/budgets/',        include('budgets.urls')),
    path('api/alertes/',        include('alertes.urls')),
    path('api/rapports/',       include('rapports.urls')),
    
]