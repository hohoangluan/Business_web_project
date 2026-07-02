"""URL config cho performance app."""
from django.urls import path
from performance.views import (
    evaluations_view,
    evaluation_hr_approval_view,
    evaluation_hr_acknowledge_action,
    evaluation_hr_reject_action,
)

urlpatterns = [
    path('evaluations/', evaluations_view, name='evaluations'),
    path('evaluations/hr-approval/', evaluation_hr_approval_view, name='evaluation_hr_approval'),
    path('evaluations/<int:pk>/acknowledge/', evaluation_hr_acknowledge_action, name='evaluation_acknowledge'),
    path('evaluations/<int:pk>/reject/', evaluation_hr_reject_action, name='evaluation_reject'),
]
