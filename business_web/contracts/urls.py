"""URL config cho contracts app."""
from django.urls import path
from contracts.views import (
    contract_view,
    hr_expiring_contracts_view,
    hr_send_reminder_view,
    hr_send_all_reminders_view,
)

urlpatterns = [
    # Nhân viên xem hợp đồng cá nhân
    path('contract/', contract_view, name='contract'),

    # HR xem danh sách hợp đồng sắp hết hạn
    path('contract/hr/expiring/', hr_expiring_contracts_view, name='hr_expiring_contracts'),

    # HR gửi nhắc nhở 1 nhân viên cụ thể (POST only)
    path('contract/hr/send-reminder/<int:user_id>/', hr_send_reminder_view, name='hr_send_reminder'),

    # HR gửi nhắc nhở tất cả (POST only)
    path('contract/hr/send-all-reminders/', hr_send_all_reminders_view, name='hr_send_all_reminders'),
]
