"""URL config cho attendance app."""
from django.urls import path

from attendance.views import (
    adjustment_approve_action,
    adjustment_reject_action,
    adjustment_review_view,
    attendance_view,
    face_check_view,
    get_image_base64_view,
    submit_adjustment_view,
    upload_image_base64_view,
)

urlpatterns = [
    path('attendance/', attendance_view, name='attendance'),
    path('attendance/upload-image/', upload_image_base64_view, name='upload_image_base64'),
    path('attendance/get-face/', get_image_base64_view, name='get_image_base64'),
    path('attendance/check/', face_check_view, name='face_check'),
    path('attendance/adjustment/<int:record_id>/', submit_adjustment_view, name='attendance_adjustment'),
    path('attendance/adjustments/review/', adjustment_review_view, name='attendance_adjustment_review'),
    path('attendance/adjustments/<int:adj_id>/approve/', adjustment_approve_action, name='attendance_adjustment_approve'),
    path('attendance/adjustments/<int:adj_id>/reject/', adjustment_reject_action, name='attendance_adjustment_reject'),
]
