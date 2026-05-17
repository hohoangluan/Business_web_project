"""URL config cho leaves app."""
from django.urls import path
from leaves.views import (
    leave_view,
    leave_approval_view,
    leave_cancel_view,
    leave_approve_action,
    leave_reject_action,
    leave_bulk_approve,
)

urlpatterns = [
    path('leave/', leave_view, name='leave'),
    path('leave/approval/', leave_approval_view, name='leave_approval'),
    path('leave/cancel/<int:pk>/', leave_cancel_view, name='leave_cancel'),
    path('leave/approve/<int:pk>/', leave_approve_action, name='leave_approve'),
    path('leave/reject/<int:pk>/', leave_reject_action, name='leave_reject'),
    path('leave/bulk-approve/', leave_bulk_approve, name='leave_bulk_approve'),
]
