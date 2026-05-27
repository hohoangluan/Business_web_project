"""URL config cho attendance app."""
from django.urls import path
from attendance.views import attendance_view
from attendance.views.image_upload_view import upload_image_base64_view, get_image_base64_view
from attendance.views.face_attendance_view import face_check_view
from attendance.views.attendance_adjustment_view import submit_adjustment_view

urlpatterns = [
    path('attendance/', attendance_view, name='attendance'),
    path('attendance/upload-image/', upload_image_base64_view, name='upload_image_base64'),
    path('attendance/get-face/', get_image_base64_view, name='get_image_base64'),
    path('attendance/check/', face_check_view, name='face_check'),
    path('attendance/adjustment/<int:record_id>/', submit_adjustment_view, name='attendance_adjustment'),
]

