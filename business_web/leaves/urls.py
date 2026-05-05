"""URL config cho leaves app."""
from django.urls import path
from leaves.views import leave_view, leave_approval_view

urlpatterns = [
    path('leave/', leave_view, name='leave'),
    path('leave/approval/', leave_approval_view, name='leave_approval'),
]
