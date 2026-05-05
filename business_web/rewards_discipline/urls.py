"""URL config cho rewards_discipline app."""
from django.urls import path
from rewards_discipline.views import rewards_penalties_view, rewards_penalties_approval_view

urlpatterns = [
    path('rewards-penalties/', rewards_penalties_view, name='rewards_penalties'),
    path('rewards-penalties/approval/', rewards_penalties_approval_view, name='rewards_penalties_approval'),
]
