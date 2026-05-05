"""URL config cho overtime app."""
from django.urls import path
from overtime.views import overtime_view, overtime_approval_view

urlpatterns = [
    path('overtime/', overtime_view, name='overtime'),
    path('overtime/approval/', overtime_approval_view, name='overtime_approval'),
]
