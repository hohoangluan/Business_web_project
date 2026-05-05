"""URL config cho contracts app."""
from django.urls import path
from contracts.views import contract_view

urlpatterns = [
    path('contract/', contract_view, name='contract'),
]
