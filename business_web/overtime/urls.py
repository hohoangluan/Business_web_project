"""URL config cho overtime app."""
from django.urls import path
from overtime.views import (
    overtime_view,
    overtime_cancel_view,
    overtime_approval_view,
    overtime_approve_action,
    overtime_reject_action,
    overtime_bulk_approve,
)

urlpatterns = [
    # Nhân viên
    path('overtime/', overtime_view, name='overtime'),
    path('overtime/cancel/<int:pk>/', overtime_cancel_view, name='overtime_cancel'),

    # Quản lý / HR
    path('overtime/approval/', overtime_approval_view, name='overtime_approval'),
    path('overtime/approve/<int:pk>/', overtime_approve_action, name='overtime_approve'),
    path('overtime/reject/<int:pk>/', overtime_reject_action, name='overtime_reject'),
    path('overtime/bulk-approve/', overtime_bulk_approve, name='overtime_bulk_approve'),
]
