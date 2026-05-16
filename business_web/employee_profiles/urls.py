"""URL config cho employee_profiles app."""
from django.urls import path
from employee_profiles.views.profile_views import (
    profile_view,
    hr_create_profile_view,
    edit_work_info_view,
    upload_document_view,
)

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('profile/upload-document/', upload_document_view, name='upload_document'),
    path('hr/create-profile/', hr_create_profile_view, name='hr_create_profile'),
    path('users/<int:user_id>/work-info/', edit_work_info_view, name='edit_work_info'),
]
