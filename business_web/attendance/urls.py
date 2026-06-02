"""URL config cho attendance app."""
from django.urls import path

from attendance.views import (
    adjustment_approve_action,
    adjustment_reject_action,
    adjustment_review_view,
    attendance_view,
    face_change_approve_action,
    face_change_image_view,
    face_change_reject_action,
    face_change_review_view,
    face_check_view,
    submit_adjustment_view,
    upload_image_base64_view,
)

urlpatterns = [
    path('attendance/', attendance_view, name='attendance'),
    path('attendance/upload-image/', upload_image_base64_view, name='upload_image_base64'),
    path('attendance/check/', face_check_view, name='face_check'),
    path('attendance/face-changes/review/', face_change_review_view, name='face_change_review'),
    path('attendance/face-changes/<int:req_id>/approve/', face_change_approve_action, name='face_change_approve'),
    path('attendance/face-changes/<int:req_id>/reject/', face_change_reject_action, name='face_change_reject'),
    path('attendance/face-changes/<int:req_id>/image/', face_change_image_view, name='face_change_image'),
    path('attendance/adjustment/<int:record_id>/', submit_adjustment_view, name='attendance_adjustment'),
    path('attendance/adjustments/review/', adjustment_review_view, name='attendance_adjustment_review'),
    path('attendance/adjustments/<int:adj_id>/approve/', adjustment_approve_action, name='attendance_adjustment_approve'),
    path('attendance/adjustments/<int:adj_id>/reject/', adjustment_reject_action, name='attendance_adjustment_reject'),
]
