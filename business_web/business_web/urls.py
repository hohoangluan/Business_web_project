"""
URL configuration for business_web project.
Include URLs từ tất cả 10 Django apps.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # App gốc: auth, dashboard, settings, admin user management
    path('', include('accounts.urls')),

    # Hồ sơ nhân viên
    path('', include('employee_profiles.urls')),

    # Hợp đồng lao động
    path('', include('contracts.urls')),

    # Chấm công
    path('', include('attendance.urls')),

    # Nghỉ phép
    path('', include('leaves.urls')),

    # Tăng ca
    path('', include('overtime.urls')),

    # Đánh giá nhân viên
    path('', include('performance.urls')),

    # Khen thưởng & Xử phạt
    path('', include('rewards_discipline.urls')),

    # Báo cáo & Tương tác
    path('', include('reports_interactions.urls')),

    # Thống kê tổng hợp
    path('', include('stats_reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

