"""URL config cho performance app."""
from django.urls import path
from performance.views import evaluations_view

urlpatterns = [
    path('evaluations/', evaluations_view, name='evaluations'),
]
