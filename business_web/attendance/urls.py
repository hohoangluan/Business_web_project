"""URL config cho attendance app."""
from django.urls import path
from attendance.views import attendance_view

urlpatterns = [
    path('attendance/', attendance_view, name='attendance'),
]
